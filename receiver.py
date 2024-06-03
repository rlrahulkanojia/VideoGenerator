import json
import time
from SQS import SQSQueue
AWS_SQS_QUEUE_NAME = "prompt_output.fifo"
# AWS_SQS_QUEUE_NAME = "staging_prompt_info.fifo"


if __name__ == "__main__":
    try:
        q = SQSQueue(queueName=AWS_SQS_QUEUE_NAME)
        while True:
            data = q.receive()
            print(data)
            time.sleep(2)
    except Exception as e:
        print(e)
