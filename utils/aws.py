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


def list_objects_in_s3(bucket, prefix):
    client = boto3.client('s3', region_name='us-west-2')
    paginator = client.get_paginator('list_objects')
    page_iterator = paginator.paginate(Bucket='galway-daily-bot-prod', Prefix='threads/')
    files = sum([page['Contents'] for page in page_iterator], [])
    files = sorted(files, key=lambda x: x['LastModified'], reverse=True)
    return files
