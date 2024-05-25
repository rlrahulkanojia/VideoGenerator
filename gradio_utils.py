import os
import cv2
import json
import requests
import subprocess
import shutil
from openai import OpenAI

api_key = "sk-proj-pKaugqFY1WJ19hSq71lrT3BlbkFJVxwwYAMxPfQGX7G3eUOi"
os.environ["OPENAI_API_KEY"]=api_key


def llm_prompt_generator(User_Input):
    os.environ["OPENAI_API_KEY"]="sk-proj-pKaugqFY1WJ19hSq71lrT3BlbkFJVxwwYAMxPfQGX7G3eUOi"
    client = OpenAI()
    # system_role =  """
    #             You are an expert in Generative AI image and Video generation
    #             Your task is to write prompts that could result in best generation of images and videos given user query
    #             User querry would be a scipt that needs to be reformatted for a well formed prompt
    #             <Important>
    #             for each user querry you needs to provide 2 prompts video prompt and image prompt
    #             User can also guide you in generating prompt by providing insights from his script
    #             Do NOT provide an introductory paragraph or sentence.
    #             Do NOT provide a conclusion.
    #             Your response should strictly be in JSON format only, with no preamble at the start or end of the JSON only fields should be Video_prompt, Image_prompt
    #             </Important>
    #             <Example1>
    #             User script: city scene of young women walking early morning in sidewalk
    #             Image_prompt:"A bustling city sidewalk scene during early morning. The street is crowded with a diverse group of people commuting. Focus on a young woman, around 25, with short brown hair, dressed in casual work attire, rushing through the crowd. The city buildings loom in the background with soft morning light filtering through"
    #             Video_prompt:"Focus on a young woman, around 25, with short brown hair, dressed in casual work attire, rushing through the crowd"

    #             <Example2>
    #             User script: women tying shoes on a bench
    #             Image_prompt:"A close-up image of a young woman, mid-20s with a lively face, sitting on a city bench. She is tying her vibrant blue Falcon Footwear sneakers. The focus is on her hands tying the laces, with blurred city movement in the background. Her expression is determined and focused."
    #             Video_prompt:"A close-up image of a young woman, mid-20s with a lively face, sitting on a city bench. She is tying her vibrant blue Falcon Footwear sneakers."

    #             <Example3>
    #             User script: women navigating crowded city street and green trail
    #             Image_prompt:"A dynamic scene showing a young woman, named Emily, navigating a crowded city street on one side, and an open, lush green trail on the other. The image should capture her in motion, half on the bustling city pavement and half on the serene trail. Her attire is sporty, suitable for both environments."
    #             Video_prompt:"A dynamic scene showing a young woman, named Emily, navigating a crowded city street on one side, and an open, lush green trail on the other."

    #             <Example4>
    #             User script: Emily stands at overlook and running on beach with friends
    #             Image_prompt:"Split scene image: On one side, Emily stands at a beautiful overlook, catching her breath with a satisfied smile. The background shows a panoramic view of nature. On the other side, she is running joyously on a sandy beach with a group of friends, all in casual sportswear, laughing and enjoying."
    #             Video_prompt:"Split scene image: On one side, Emily stands at a beautiful overlook, catching her breath with a satisfied smile. The background shows a panoramic view of nature."

    #             <Example5>
    #             User script: Emily and friends playing basketball in urban park
    #             Image_prompt:"An outdoor basketball court scene with Emily and her friends playing basketball. The court is in an urban park. Emily is actively participating in the game, wearing her Falcon Footwear sneakers. The focus is on the action and the energy of the game, with city buildings in the distant background."
    #             Video_prompt:"An outdoor basketball court scene with Emily and her friends playing basketball. The court is in an urban park."

    #             <Example6>
    #             User script: Emily in cozy café wearing Falcon Footwear
    #             Image_prompt:"A warm, inviting image of Emily sitting comfortably in a cozy café, looking out of the window with a thoughtful expression. She's wearing her Falcon Footwear, casually crossed at the ankle. The interior is stylish and modern, suggesting a moment of reflection after a day full of adventures."
    #             Video_prompt:"A warm, inviting image of Emily sitting comfortably in a cozy café, looking out of the window with a thoughtful expression. She's wearing her Falcon Footwear, casually crossed at the ankle."

    #             <Example7>
    #             User script: Falcon Footwear sneakers on wooden floor
    #             Image_prompt:"A simple, elegant image of the Falcon Footwear sneakers on a wooden floor. The lighting focuses on the sneakers, highlighting their vibrant blue color and sleek design. The background is a soft, blurred image of a city skyline during sunset, emphasizing the brand’s urban appeal."
    #             Video_prompt:"A simple, elegant image of the Falcon Footwear sneakers on a wooden floor."

    #             """
    
    system_role = """
                Read through the provided text prompt carefully. Rewrite it into a single plain English description that objectively and literally depicts the key visual elements - the setting, characters, objects, actions and events occurring. Use straightforward language to factually describe what needs to be shown without any subjective interpretation, metaphorical framing, or creative embellishments. The goal is a clear, unambiguous prompt that can be directly translated into a video representation of the original narrative content. Stick to just the objective details that are visually representable.
                Your task is to write prompts that could result in best generation of images and videos given user query
                Do NOT provide an introductory paragraph or sentence.
                Do NOT provide a conclusion.
                Elaborate the statement with real life examples if the contet provided by user is not clear.
                Your response should strictly be in JSON format only, with no preamble at the start or end of the JSON only fields should be a "prompt".
                """
    
    user_query=f"""
            {User_Input}
            """
    completion_response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": system_role},
        {"role": "user", "content": user_query}
    ],
    temperature=0.0,
    response_format={"type":"json_object"}
    )
    output=completion_response.choices[0].message.content
    while 1:
        try:
            output=json.loads(output)
            break
        except:
            pass

    return output

class Generator:

    def __init__(self, image_prompt, video_prompt, file_path):
        self.name = "Generator"
        self.image_prompt = image_prompt
        self.video_prompt = video_prompt
        self.file_path = file_path + ".txt"
        self.image_name = "data/test_images/" + file_path + ".jpg"
        self.command = [
                    'python', 'inference.py',
                    '--cfg', 'configs/i2vgen_xl_infer.yaml',
                    'test_list_path', self.file_path,
                    'test_model', 'models/i2vgen_xl_00854500.pth'
                ]

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
          prompt=self.image_prompt,
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
        test_data = f"{self.image_name}|||{self.video_prompt}"
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

    def run_iterations(self, number_of_iterations=1):
        print("Generating Image from Dalle-3")
        self.image_generator()
        print("Creating Input list")
        self.create_input_list()

        print("Removing earlier generated video")
        self.clear_directory('/root/VGen/workspace/experiments/gradio_test')
        
        print("Runnning video generation")
        # subprocess.run(self.command) 

    
        for i in range(number_of_iterations):
            # Execute the command
            subprocess.run(self.command)
            
            # Print completion message
            print(f"Run {i+1} of the script completed")
        
            # Specify the directory
            directory = f"workspace/experiments/{self.file_path.split('.')[0]}/"
            
            # Get list of files in the directory
            files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and 'log' not in f]
            
            
            # Find the latest file
            latest_file = max(files, key=os.path.getctime)
            new_name = os.path.join(directory, f'{i+1}.mp4')
            
            # Rename the latest file
            os.rename(latest_file, new_name)
            
            print(f'Renamed "{latest_file}" to "{new_name}"')    

            self.save_last_frame(new_name)
            print(f"Saved Last Video at {new_name}")


        self.combine_videos()


    def clear_directory(self, directory):
        if os.path.exists(directory):
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                os.remove(item_path)

    def combine_videos(self):
        os.system("/root/VGen/combine_videos.sh output.mp4")
     
    def combine_videos_old(self):
        
        # Path to the folder containing the videos
        folder_path = "workspace/experiments/" + self.file_path.split(".")[0]
        # Get list of video files in the folder
        video_files = [f for f in os.listdir(folder_path) if f.endswith('.mp4')]
        
        # Sort video files based on their names (assuming they are named numerically)
        video_files.sort()
        
        # Initialize an empty list to store video frames

        # Concatenate frames vertically (assuming all videos have the same resolution
        os.makedirs("gradio_videos", exist_ok=True)
        # Write the concatenated video to a file
        output_path = "gradio_videos/"+ self.video_prompt[:60] +".mp4"
        fourcc = cv2.VideoWriter_fourcc(*'xvid') # Specify the codec
        # fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # for MP4 codec
        out = cv2.VideoWriter(output_path, fourcc, 8, (1280, 704))
        
        # Read each video and store frames
        for video_file in video_files:
            print(video_file)
            video_path = os.path.join(folder_path, video_file)
            video_capture = cv2.VideoCapture(video_path)
        
            while True:
                success, frame = video_capture.read()
                if not success:
                    break
                out.write(frame)
                print(frame.shape)
        
            # Release video capture object after reading the video
            video_capture.release()
        
        # # Release the VideoWriter
        out.release()
            
        print("Concatenated video saved successfully!")
        print("=======================================================================================")
