import uuid
from SQS import Downloader

if __name__ == "__main__":
    q = Downloader()
    jobID = "05560918-28ee-4e7e-a205-fea5329f55b3"
    q.download(jobID)