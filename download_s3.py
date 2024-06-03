import boto3

if __name__ == "__main__":
    jobID = "05560918-28ee-4e7e-a205-fea5329f55b3"
    s3_access = boto3.resource('s3', region_name='ap-south-1',
                                        aws_access_key_id="AKIA3FLD52CJXFCX4BNE",
                                        aws_secret_access_key="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")
    s3_access.Bucket("phase1video").download_file('05560918-28ee-4e7e-a205-fea5329f55b3.mp4', '05560918-28ee-4e7e-a205-fea5329f55b3.mp4')