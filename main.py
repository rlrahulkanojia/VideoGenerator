import time
from SQS import SQSQueue
from gradio_utils import Generator, llm_prompt_generator

AWS_SQS_QUEUE_NAME = "prompt_input.fifo"

class Main:
    
    def __init__(self):
        self.queue_checker = SQSQueue(AWS_SQS_QUEUE_NAME)

    def process_prompt(self, message):

        video_path = None
        duration = int(message["duration"]) // 4
        prompts = llm_prompt_generator(message["prompt"])
        image_prompt = prompts["prompt"]
        video_prompt = prompts["prompt"]
            
        generator = Generator(
                    image_prompt=image_prompt,
                    video_prompt=video_prompt,
                    file_path="gradio_test"
                )
        generator.run_iterations(duration)
        

    def run(self):

        while True:
            print("Checking Message..")
            message = self.queue_checker.receive()
            if message is not None:
                print("Processing Message : ", message)
                self.process_prompt(message)

            time.sleep(2)

if __name__ == "__main__":
    main = Main()
    try:
        main.run()
    except Exception as e:
        print(f"Error while processing prompt {e}")