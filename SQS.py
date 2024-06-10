import boto3
import os
import sys
import json

from dotenv import load_dotenv
load_dotenv()

AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
 
class SQSQueue(object):
 
    def __init__(self, queueName=None):
        self.resource = boto3.resource('sqs', region_name='ap-south-1',
                                       aws_access_key_id=AWS_ACCESS_KEY,
                                       aws_secret_access_key=AWS_SECRET_KEY)
        self.queue = self.resource.get_queue_by_name(QueueName=queueName)
        self.QueueName = queueName
        self.s3_access = boto3.resource('s3', region_name='ap-south-1',
                                       aws_access_key_id=AWS_ACCESS_KEY,
                                       aws_secret_access_key=AWS_SECRET_KEY)
 
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

class SQSQueueStandard(object):
 
    def __init__(self, queueName=None):
        self.resource = boto3.resource('sqs', region_name='ap-south-1',
                                       aws_access_key_id=AWS_ACCESS_KEY,
                                       aws_secret_access_key=AWS_SECRET_KEY)
        self.queue = self.resource.get_queue_by_name(QueueName=queueName)
        self.QueueName = queueName
        self.s3_access = boto3.resource('s3', region_name='ap-south-1',
                                       aws_access_key_id=AWS_ACCESS_KEY,
                                       aws_secret_access_key=AWS_SECRET_KEY)
 
    def send(self, Message={}, jobID=None):
        data = json.dumps(Message)
        response = self.queue.send_message(MessageBody=data)
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

class Downloader(object):
 
    def __init__(self):
        self.s3_access = boto3.client('s3', region_name='ap-south-1',
                                       aws_access_key_id=AWS_ACCESS_KEY,
                                       aws_secret_access_key=AWS_SECRET_KEY)
    def download(self, jobID):
        bucket_name = "phase1video"
        object_key = f"{jobID}.mp4"
        local_file_path = "test_output.mp4"
        self.s3_access.download_file(bucket_name, object_key, local_file_path)
 
 
if __name__ == "__main__":
    queueName = "prompt_input.fifo"
    q = SQSQueue(queueName=queueName)
    jobID = "0001"
    Message = {"jobID":jobID,
               "prompt":"hello there"}
    response = q.send(Message=Message, jobID=jobID)
    print(response)
    data = q.receive()
    print(data)