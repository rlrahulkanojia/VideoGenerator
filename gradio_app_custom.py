import sys
import gradio as gr
from gradio_utils import Generator, llm_prompt_generator

class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        
    def flush(self):
        self.terminal.flush()
        self.log.flush()
        
    def isatty(self):
        return False    

sys.stdout = Logger("output.log")

def read_logs():
    sys.stdout.flush()
    with open("output.log", "r") as f:
        return f.read()

def process_input(prompt, duration):

    video_path = None
    image_prompt = prompt
    video_prompt = prompt
    duration = duration // 4
    generated_prompts = llm_prompt_generator(prompt)
    image_prompt = generated_prompts["Image_prompt"]
    video_prompt = generated_prompts["Video_prompt"]
        
    generator = Generator(
                image_prompt=image_prompt,
                video_prompt=video_prompt,
                file_path="gradio_test"
            )
    generator.run_iterations(duration)
    video_path = "/root/VGen/workspace/experiments/gradio_test/output.mp4"
    return video_path

with gr.Blocks() as demo:
    with gr.Row():
        prompt = gr.Textbox(label="Enter Prompt")
        duration = gr.Dropdown(choices=[4, 8, 12, 16, 20], label="Select Duration of video")
        interface = gr.Interface(
            fn=process_input,
            inputs=[prompt, duration],
            outputs=gr.Video(label="Result Video"),
        )
        logs = gr.Textbox(label="Logs")
        demo.load(read_logs, None, logs, every=1)

        print("Iteration executed successfuly...")
    
demo.queue().launch(share=True)
