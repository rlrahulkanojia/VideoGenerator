import boto3
import os
import sys
import json

AWS_SQS_QUEUE_NAME = "prompt_input.fifo"
 
 
class SQSQueue(object):
 
    def __init__(self, queueName=None):
        self.resource = boto3.resource('sqs', region_name='ap-south-1',
                                       aws_access_key_id="<>",
                                       aws_secret_access_key="<>")
        self.queue = self.resource.get_queue_by_name(QueueName=AWS_SQS_QUEUE_NAME)
        self.QueueName = queueName
 
    def send(self, Message={}, jobID=None):
        data = json.dumps(Message)
        response = self.queue.send_message(MessageBody=data,
                                           MessageGroupId = jobID,
                                           MessageDeduplicationId = jobID)
        return response
 
    def receive(self):
        try:
            queue = self.resource.get_queue_by_name(QueueName=self.QueueName)
            for message in queue.receive_messages():
                data = message.body
                data = json.loads(data)
                message.delete()
                return data
        except Exception as e:
            print(e)
            return []
 
 
if __name__ == "__main__":
    q = SQSQueue(queueName=AWS_SQS_QUEUE_NAME)
    jobID = "0001"
    Message = {"jobID":jobID,
               "prompt":"hello there"}
    response = q.send(Message=Message, jobID=jobID)
    print(response)
    data = q.receive()
    print(data)