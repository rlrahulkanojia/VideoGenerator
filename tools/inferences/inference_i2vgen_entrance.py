'''
/* 
*Copyright (c) 2021, Alibaba Group;
*Licensed under the Apache License, Version 2.0 (the "License");
*you may not use this file except in compliance with the License.
*You may obtain a copy of the License at

*   http://www.apache.org/licenses/LICENSE-2.0

*Unless required by applicable law or agreed to in writing, software
*distributed under the License is distributed on an "AS IS" BASIS,
*WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*See the License for the specific language governing permissions and
*limitations under the License.
*/
'''

import os
import re
import os.path as osp
import sys
sys.path.insert(0, '/'.join(osp.realpath(__file__).split('/')[:-4]))
import json
import math
import uuid
import torch
import random
import pynvml
import logging
import numpy as np
from PIL import Image
from tqdm import tqdm
import torch.cuda.amp as amp
from importlib import reload
import torch.distributed as dist
import torch.multiprocessing as mp

from einops import rearrange
import torchvision.transforms as T
import torchvision.transforms.functional as TF
from torch.nn.parallel import DistributedDataParallel

import utils.transforms as data
from ..modules.config import cfg
from utils.seed import setup_seed
from utils.multi_port import find_free_port
from utils.assign_cfg import assign_signle_cfg
from utils.distributed import generalized_all_gather, all_reduce
from utils.video_op import save_i2vgen_video, save_i2vgen_video_safe
from utils.registry_class import INFER_ENGINE, MODEL, EMBEDDER, AUTO_ENCODER, DIFFUSION


### Custom code:
import cv2
import time
import requests
from openai import OpenAI
from SQS import SQSQueue, SQSQueueStandard
from gradio_utils import llm_prompt_generator

### Variables

input_queue_listener = SQSQueue("prompt_input.fifo")
logging_queue = SQSQueueStandard("logging")
output_queue = SQSQueue("prompt_output.fifo")

### Paths
BUCKET = "phase1video"
img_key = "/root/VideoGenerator/data/test_images/tutorial.jpg"
video_suffix = "/root/VideoGenerator/workspace/experiments/tutorial/"
LOG_DIR = "/root/VideoGenerator/workspace/experiments/tutorial/"


@INFER_ENGINE.register_function()
def inference_i2vgen_entrance(cfg_update,  **kwargs):
    for k, v in cfg_update.items():
        if isinstance(v, dict) and k in cfg:
            cfg[k].update(v)
        else:
            cfg[k] = v
    
    if not 'MASTER_ADDR' in os.environ:
        os.environ['MASTER_ADDR']='localhost'
        os.environ['MASTER_PORT']= find_free_port()
    cfg.pmi_rank = int(os.getenv('RANK', 0)) 
    cfg.pmi_world_size = int(os.getenv('WORLD_SIZE', 1))
    
    if cfg.debug:
        cfg.gpus_per_machine = 1
        cfg.world_size = 1
    else:
        cfg.gpus_per_machine = torch.cuda.device_count()
        cfg.world_size = cfg.pmi_world_size * cfg.gpus_per_machine
    
    if cfg.world_size == 1:
        worker(0, cfg, cfg_update)
    else:
        mp.spawn(worker, nprocs=cfg.gpus_per_machine, args=(cfg, cfg_update))
    return cfg


def worker(gpu, cfg, cfg_update):
    '''
    Inference worker for each gpu
    '''
    cfg = assign_signle_cfg(cfg, cfg_update, 'vldm_cfg')
    for k, v in cfg_update.items():
        if isinstance(v, dict) and k in cfg:
            cfg[k].update(v)
        else:
            cfg[k] = v

    cfg.gpu = gpu
    cfg.seed = int(cfg.seed)
    cfg.rank = cfg.pmi_rank * cfg.gpus_per_machine + gpu
    setup_seed(cfg.seed + cfg.rank)

    if not cfg.debug:
        torch.cuda.set_device(gpu)
        torch.backends.cudnn.benchmark = True
        dist.init_process_group(backend='nccl', world_size=cfg.world_size, rank=cfg.rank)

    # [Log] Save logging and make log dir
    log_dir = generalized_all_gather(cfg.log_dir)[0]
    exp_name = osp.basename(cfg.test_list_path).split('.')[0]
    inf_name = osp.basename(cfg.cfg_file).split('.')[0]
    test_model = osp.basename(cfg.test_model).split('.')[0].split('_')[-1]
    
    cfg.log_dir = osp.join(cfg.log_dir, '%s' % (exp_name))
    os.makedirs(cfg.log_dir, exist_ok=True)
    log_file = osp.join(cfg.log_dir, 'log_%02d.txt' % (cfg.rank))
    cfg.log_file = log_file
    reload(logging)
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(filename=log_file),
            logging.StreamHandler(stream=sys.stdout)])
    logging.info(cfg)
    logging.info(f"Going into it2v_fullid_img_text inference on {gpu} gpu")
    
    # [Diffusion]
    diffusion = DIFFUSION.build(cfg.Diffusion)

    # [Data] Data Transform    
    train_trans = data.Compose([
        data.CenterCropWide(size=cfg.resolution),
        data.ToTensor(),
        data.Normalize(mean=cfg.mean, std=cfg.std)])
    
    vit_trans = data.Compose([
        data.CenterCropWide(size=(cfg.resolution[0], cfg.resolution[0])),
        data.Resize(cfg.vit_resolution),
        data.ToTensor(),
        data.Normalize(mean=cfg.vit_mean, std=cfg.vit_std)])

    # [Model] embedder
    clip_encoder = EMBEDDER.build(cfg.embedder)
    clip_encoder.model.to(gpu)
    _, _, zero_y = clip_encoder(text="")
    _, _, zero_y_negative = clip_encoder(text=cfg.negative_prompt)
    zero_y, zero_y_negative = zero_y.detach(), zero_y_negative.detach()
    black_image_feature = torch.zeros([1, 1, cfg.UNet.y_dim]).cuda()

    # [Model] auotoencoder 
    autoencoder = AUTO_ENCODER.build(cfg.auto_encoder)
    autoencoder.eval() # freeze
    for param in autoencoder.parameters():
        param.requires_grad = False
    autoencoder.cuda()

    # [Model] UNet 
    model = MODEL.build(cfg.UNet)
    checkpoint_dict = torch.load(cfg.test_model, map_location='cpu')
    state_dict = checkpoint_dict['state_dict']
    resume_step = checkpoint_dict['step']
    status = model.load_state_dict(state_dict, strict=True)
    logging.info('Load model from {} with status {}'.format(cfg.test_model, status))
    model = model.to(gpu)
    model.eval()
    model = DistributedDataParallel(model, device_ids=[gpu]) if not cfg.debug else model
    torch.cuda.empty_cache()
    
    while True:
        unique_string = uuid.uuid4().hex.upper()[0:9]
        # print("Checking Message..")
        message = input_queue_listener.receive()

        # message = {
        #     "duration": 12,
        #     "jobID": "testing",
        #     "prompt": "A frog in the pond.",
        # }

        if message is not None:
            print("Message received: ", message)

            if check_message(message) is True:
                # Logging
                try:
                    clear_files(LOG_DIR)
                except Exception as e:
                    print("Error in clearing files", str(e))

                logging_queue.send(Message=message) 

                prompts = llm_prompt_generator(message["prompt"])
                message["duration"] = int(message["duration"])

                try:

                    for i in range(1, message["duration"]//4 + 1):

                        print(f"Starting Generating video... {i}/{message['duration']//4}")

                        if i == 1:
                            image_generator(prompts["Image_prompt"])
                        else:
                            extract_last_image(i-1)

                        img_name = os.path.basename(img_key).split('.')[0]
                        image = Image.open(img_key)
                        caption = prompts["Video_prompt"]
                        captions = [caption]

                        if image.mode != 'RGB':
                            image = image.convert('RGB')
                        with torch.no_grad():
                            image_tensor = vit_trans(image)
                            image_tensor = image_tensor.unsqueeze(0)
                            y_visual, y_text, y_words = clip_encoder(image=image_tensor, text=captions)
                            y_visual = y_visual.unsqueeze(1)

                        fps_tensor =  torch.tensor([cfg.target_fps], dtype=torch.long, device=gpu)
                        image_id_tensor = train_trans([image]).to(gpu)
                        local_image = autoencoder.encode_firsr_stage(image_id_tensor, cfg.scale_factor).detach()
                        local_image = local_image.unsqueeze(2).repeat_interleave(repeats=cfg.max_frames, dim=2)

                        with torch.no_grad():
                            pynvml.nvmlInit()
                            handle=pynvml.nvmlDeviceGetHandleByIndex(0)
                            meminfo=pynvml.nvmlDeviceGetMemoryInfo(handle)
                            logging.info(f'GPU Memory used {meminfo.used / (1024 ** 3):.2f} GB')
                            # Sample images
                            with amp.autocast(enabled=cfg.use_fp16):
                                # NOTE: For reproducibility, we have alread recorde the seed ``cur_seed''
                                # torch.manual_seed(cur_seed) 
                                # cur_seed = torch.get_rng_state()[0]
                                # logging.info(f"Current seed {cur_seed}...")
                                noise = torch.randn([1, 4, cfg.max_frames, int(cfg.resolution[1]/cfg.scale), int(cfg.resolution[0]/cfg.scale)])
                                noise = noise.to(gpu)
                                
                                infer_img = black_image_feature if cfg.use_zero_infer else None
                                model_kwargs=[
                                    {'y': y_words, 'image':y_visual, 'local_image':local_image, 'fps': fps_tensor}, 
                                    {'y': zero_y_negative, 'image':infer_img, 'local_image':local_image, 'fps': fps_tensor}]
                                video_data = diffusion.ddim_sample_loop(
                                    noise=noise,
                                    model=model.eval(),
                                    model_kwargs=model_kwargs,
                                    guide_scale=cfg.guide_scale,
                                    ddim_timesteps=cfg.ddim_timesteps,
                                    eta=0.0)
                                
                        video_data = 1. / cfg.scale_factor * video_data # [1, 4, 32, 46]
                        video_data = rearrange(video_data, 'b c f h w -> (b f) c h w')
                        chunk_size = min(cfg.decoder_bs, video_data.shape[0])
                        video_data_list = torch.chunk(video_data, video_data.shape[0]//chunk_size, dim=0)
                        decode_data = []
                        for vd_data in video_data_list:
                            gen_frames = autoencoder.decode(vd_data)
                            decode_data.append(gen_frames)
                        video_data = torch.cat(decode_data, dim=0)
                        video_data = rearrange(video_data, '(b f) c h w -> b c f h w', b = cfg.batch_size)
                        
                        text_size = cfg.resolution[-1]
                        file_name = f'{i}.mp4'
                        local_path = os.path.join(LOG_DIR, f'{file_name}')
                        os.makedirs(os.path.dirname(local_path), exist_ok=True)

                        try:
                            save_i2vgen_video_safe(local_path, video_data.cpu(), captions, unique_string,  cfg.mean, cfg.std, text_size)
                            logging.info('Save video to dir %s:' % (local_path))
                        except Exception as e:
                            logging.info(f'Step: save text or video error with {e}')

                        print("Generating Video.. ", message)

                    combine_videos()
                    post_process(message["jobID"], status="success", error="")
                    upload_video(message["jobID"])
                    logging.info('Congratulations! The inference is completed!')
                
                except Exception as r:
                    print("Error in Video Generation", str(r))
                    message["status"] = "failed"
                    message["description"] = str(r)
                    logging_queue.send(Message=message)

            else:
                print("Invalid message", message)
                message["status"] = "failed"
                message["description"] = "Duration must be among 4, 8, 12."
                logging_queue.send(Message=message)
                
       
        if not cfg.debug:
            torch.cuda.synchronize()
            dist.barrier()


        time.sleep(2)



def check_message(message):
    try:
        if str(message["duration"]) not in ["4", "8", "12"]:
            print("Invalid message")
            return False
        if "jobID" not in message.keys():
            return False
    except Exception as e:
        print("Error ", e)
        return False
    return True


def post_process(jobID, status, error):
        Message = {"jobID":jobID,
                   "status":status,
                   "s3_path":f"s3://phase1video/{jobID}.mp4",
                   "description": str(error)}
        print("Output Message ", Message)
        logging_queue.send(Message=Message)
        output_queue.send(Message=Message, jobID=jobID) 
        print("Uploaded to Queue.")

def upload_video(jobID):
    print("Uploading Video to s3")
    input_queue_listener.s3_access.Bucket(BUCKET).upload_file("/root/VideoGenerator/workspace/experiments/tutorial/output.mp4", f"{jobID}.mp4")
    print("Uploaded Video to s3")  

def image_generator(image_prompt):
    """
    Generates an image from a prompt using OpenAI's API and saves it locally.

    Parameters:
    - prompt (str): The prompt to generate the image from.
    - filename (str): The local filename to save the image.
    """
    # Call the OpenAI API to generate the image
    response = OpenAI().images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    # Get the image URL from the response
    image_url = dict(response)['data'][0].url

    # Download the image from the URL
    image_response = requests.get(image_url)

    # Save the image to a file
    with open(img_key, 'wb') as file:
        file.write(image_response.content)

    print(f"Image saved as {img_key}")

def extract_last_image(k):

    # Capture video
    path = video_suffix+str(k)+".mp4"
    cap = cv2.VideoCapture(path)

    if not cap.isOpened():
        print("Error: Couldn't open video file.", path)
        return

    last_frame = None

    # Read through the video
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        last_frame = frame

    # Save the last frame
    if last_frame is not None:
        cv2.imwrite(img_key, last_frame)
        print(f"Last frame saved to {img_key}")
    else:
        print("No frames to save.")

    # Release resources
    cap.release()

def clear_files(directory):
    print("Clearing logging diretory")
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            os.unlink(item_path) # Delete the now-empty directory

def combine_videos():
    os.system("/root/VideoGenerator/combine_videos.sh output.mp4")

