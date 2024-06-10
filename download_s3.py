import os
import boto3

from dotenv import load_dotenv
load_dotenv()

AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')

if __name__ == "__main__":
    jobID = "05560918-28ee-4e7e-a205-fea5329f55b3"
    s3_access = boto3.resource('s3', region_name='ap-south-1',
                                        aws_access_key_id=AWS_ACCESS_KEY,
                                        aws_secret_access_key=AWS_SECRET_KEY)
    s3_access.Bucket("phase1video").download_file('05560918-28ee-4e7e-a205-fea5329f55b3.mp4', '05560918-28ee-4e7e-a205-fea5329f55b3.mp4')