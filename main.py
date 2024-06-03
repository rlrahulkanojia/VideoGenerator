import time
import boto3
from SQS import SQSQueue, SQSQueueStandard
from gradio_utils import Generator, llm_prompt_generator

BUCKET = "phase1video"

class Main:
    
    def __init__(self):
        self.queue_checker = SQSQueue("prompt_input.fifo")
        self.logging_queue = SQSQueueStandard("logging")
        self.output_queue = SQSQueue("prompt_output.fifo")

    def create_video(self, message):

        try:
            video_path = None
            duration = int(message["duration"]) // 4
            prompts = llm_prompt_generator(message["prompt"])
            image_prompt = prompts["Image_prompt"]
            video_prompt = prompts["Video_prompt"]
                
            generator = Generator(
                        image_prompt=image_prompt,
                        video_prompt=video_prompt,
                        file_path="gradio_test"
                    )
            print("Running Iteration..")
            status = generator.run_iterations(duration)

            if status is False:
                return "Failed", str(generator.errors)

            return "Success", []
        except Exception as e:
            return "Failed", str(e)
            

    def run(self):

        while True:

            try:
                print("Checking Message..")
                message = self.queue_checker.receive()
                if message is not None:
                    if self.check_message(message) is True:
                        # Logging
                        self.logging_queue.send(Message=message) 
                        
                        print("Generating Video.. ", message)
                        status, error = self.create_video(message)
                        print("Uploading Video..")
    
                        if error == []:
                            self.upload_video(message["jobID"])
                        
                        print("Post Processing..")
                        self.post_process(message["jobID"], status, error)
    
                    else:
                        message["status"] = "failed"
                        message["description"] = "Duration must be among 4, 8, 12."
                        self.logging_queue.send(Message=message) 
    
                time.sleep(2)
                
            except Exception as e:
                message = {}
                message["status"] = "failed"
                message["description"] = str(e)
                print(message)
                self.logging_queue.send(Message=message) 
            


    def post_process(self, jobID, status, error):
        Message = {"jobID":jobID,
                   "status":status,
                   "s3_path":f"s3://phase1video/{jobID}.mp4",
                   "description": str(error)}
        print("Output Message ", Message)
        self.logging_queue.send(Message=Message)
        self.output_queue.send(Message=Message, jobID=jobID) 
        print("Uploaded to Queue.")


    def upload_video(self, jobID):
        print("Uploading Video to s3")
        self.queue_checker.s3_access.Bucket(BUCKET).upload_file("/root/VideoGenerator/workspace/experiments/gradio_test/output.mp4", f"{jobID}.mp4")
        print("Uploaded Video to s3")  

    def check_message(self, message):
        try:
            if message["duration"] not in [4, 8, 12]:
                print("Invalid message")
                return False
        except:
            return False
        return True



if __name__ == "__main__":
    main = Main()
    main.run()