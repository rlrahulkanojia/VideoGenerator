import os
import yaml
import cv2
import base64
import requests
os.environ["REPLICATE_API_TOKEN"]="r8_N02JyR5WFnFG3DdksK9cuktBgmm9tP41kDXLj"
import replicate
import subprocess

api_key = "sk-proj-pKaugqFY1WJ19hSq71lrT3BlbkFJVxwwYAMxPfQGX7G3eUOi"
os.environ["OPENAI_API_KEY"]=api_key
from openai import OpenAI


class Generator_9secs:

    def __init__(self, prompt):
        self.name = "Generator"
        self.prompt = prompt
        self.file_path = '18_sec_smooth.txt'
        self.image_name = "data/test_images/18_sec_smooth.jpg"
        self.command = [
                    'python', 'inference.py',
                    '--cfg', 'configs/i2vgen_xl_infer_smooth.yaml',
                    'test_list_path', self.file_path,
                    'test_model', 'models/i2vgen_xl_00854500.pth'
                ]
        with open("configs/i2vgen_xl_infer_smooth.yaml") as f:
            list_doc = yaml.safe_load(f)
            list_doc["guide_scale"] = 9

        with open("configs/i2vgen_xl_infer_smooth.yaml", "w") as f:
            yaml.dump(list_doc, f)

    def image_generator(self):
        """
        Generates an image from a prompt using OpenAI's API and saves it locally.
    
        Parameters:
        - prompt (str): The prompt to generate the image from.
        - filename (str): The local filename to save the image.
        """
        # Call the OpenAI API to generate the image
        response = OpenAI().images.generate(
          model="dall-e-3",
          prompt=self.prompt,
          size="1024x1024",
          quality="standard",
          n=1,
        )
    
        # Get the image URL from the response
        image_url = dict(response)['data'][0].url
    
        # Download the image from the URL
        image_response = requests.get(image_url)
    
        # Save the image to a file
        with open(self.image_name, 'wb') as file:
            file.write(image_response.content)
    
        print(f"Image saved as {self.image_name}")

    def create_input_list(self):
        test_data = f"{self.image_name}|||{self.prompt}"
        # Open the file in write mode ('w') which will create the file if it doesn't exist
        with open(self.file_path, 'w') as file:
            # Write the string to the file
            file.write(test_data)

    def save_last_frame(self, video_path):
    
        # Capture video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Couldn't open video file.")
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
            cv2.imwrite(self.image_name, last_frame)
            print(f"Last frame saved to {self.image_name}")
        else:
            print("No frames to save.")
    
        # Release resources
        cap.release()

    def run_iterations(self, number_of_iterations=2):
        print("Generating Image from Dalle-3")
        self.image_generator()
        print("Creating Input list")
        self.create_input_list()

        print("Removing earlier generated video")
        try:
            subprocess.run("rm -rf workspace/experiments/18_sec_smooth/")
        except:
            print("Folder not created yet.")
        
        print("Runnning video generation")
        # subprocess.run(self.command) 

    
        for i in range(number_of_iterations):

            with open("configs/i2vgen_xl_infer_smooth.yaml") as f:
                list_doc = yaml.safe_load(f)
                print("Running Iteration with guidance scale : ",list_doc["guide_scale"])

            print("Running...")
            # Execute the command
            subprocess.run(self.command)
            
            # Print completion message
            print(f"Run {i+1} of the script completed")
        
            # Specify the directory
            directory = 'workspace/experiments/18_sec_smooth/'
            
            # Get list of files in the directory
            files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and 'log' not in f]
            
            
            # Find the latest file
            latest_file = max(files, key=os.path.getctime)
            new_name = os.path.join(directory, f'{i+1}.mp4')
            
            # Rename the latest file
            os.rename(latest_file, new_name)
            
            print(f'Renamed "{latest_file}" to "{new_name}"')    

            self.save_last_frame(new_name)
            print("Denoising Image")
            self.denoise_image()
            print("Denoised Image")
            
            print(f"Saved frame from {new_name}")
    
            with open("configs/i2vgen_xl_infer_smooth.yaml") as f:
                list_doc = yaml.safe_load(f)
                list_doc["guide_scale"] = max(1, list_doc["guide_scale"] // 1.5)
            
            with open("configs/i2vgen_xl_infer_smooth.yaml", "w") as f:
                yaml.dump(list_doc, f)
                    
        

        self.combine_videos()

    def denoise_image(self):

        with open(self.image_name, 'rb') as file:
          data = base64.b64encode(file.read()).decode('utf-8')
          image = f"data:application/octet-stream;base64,{data}"
        
        input = {
            "image": image,
            "task_type": "Image Denoising"
        }
        
        output = replicate.run(
            "megvii-research/nafnet:018241a6c880319404eaa2714b764313e27e11f950a7ff0a7b5b37b27b74dcf7",
            input=input
        )
        data = requests.get(output).content 
        f = open(self.image_name,'wb') 
        f.write(data) 
        f.close() 
        print("Replaced image with denoised image")
          
    def combine_videos(self):
        
        # Path to the folder containing the videos
        folder_path = "workspace/experiments/18_sec_smooth"
        
        # Get list of video files in the folder
        video_files = [f for f in os.listdir(folder_path) if f.endswith('.mp4')]
        
        # Sort video files based on their names (assuming they are named numerically)
        video_files.sort()
        
        # Initialize an empty list to store video frames
        frames = []
        
        # Read each video and store frames
        for video_file in video_files:
            print(video_file)
            video_path = os.path.join(folder_path, video_file)
            video_capture = cv2.VideoCapture(video_path)
        
            while True:
                success, frame = video_capture.read()
                if not success:
                    break
                frames.append(frame)
        
            # Release video capture object after reading the video
            video_capture.release()
        
        # Concatenate frames vertically (assuming all videos have the same resolution

        os.makedirs("18_sec_smooth", exist_ok = True)
        
        # Write the concatenated video to a file
        output_path = "18_sec_smooth/" + str(self.prompt)+".mp4"
        # fourcc = cv2.VideoWriter_fourcc(*'xvid') # Specify the codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # for MP4 codec
        height, width, _ = frames[0].shape  # Get the dimensions from the first frame
        out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), 8, (width, height))
        
        for frame in frames:
            out.write(frame)
        
        # Release the VideoWriter
        out.release()
        
        print("Concatenated video saved successfully!")



prompt = "a real dog walking slowly along the california beach in sunset."
print(f"Prompt : {prompt}")
generator = Generator_9secs(prompt)

generator.command = [
                'python', 'inference.py',
                '--cfg', 'configs/i2vgen_xl_infer_smooth.yaml',
                'test_list_path', generator.file_path,
                'test_model', 'models/i2vgen_xl_00854500.pth'
            ]

generator.run_iterations(number_of_iterations=5) #Each iteration increases the video duration by 4 secs ( 32 frames ).


       