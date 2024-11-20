import boto3


def read_file_from_s3(bucket, key):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket, Key=key)
    return response['Body'].read().decode('utf-8')


def write_file_to_s3(bucket, key, data):
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket, Key=key, Body=data)


def file_exists_in_s3(bucket, key):
    s3 = boto3.client('s3')
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except:
        return False
