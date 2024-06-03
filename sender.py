import uuid
from SQS import SQSQueue
AWS_SQS_QUEUE_NAME = "prompt_input.fifo"
# AWS_SQS_QUEUE_NAME = "prompt_output.fifo"

if __name__ == "__main__":
    q = SQSQueue(queueName=AWS_SQS_QUEUE_NAME)
    jobID = str(uuid.uuid4())
    print("JobID ", jobID)
    Message = {"jobID":jobID,
               "duration":4,
               "prompt":"A frog in the pond."}
    response = q.send(Message=Message, jobID=jobID)
    print(response)