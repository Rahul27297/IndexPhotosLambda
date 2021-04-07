import json
import boto3
import datetime
import requests
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection

def detect_labels(photo, bucket):
    client = boto3.client('rekognition')

    # get labels from amazon rekognition service
    response = client.detect_labels(Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
                                    MaxLabels=10, MinConfidence=75)

    labels = []
    for label in response['Labels']:
        labels.append(label['Name'])

    return labels


def lambda_handler(event, context):
    print(event)
    print(event["Records"][0]["s3"]["bucket"])
    print(event["Records"][0]["s3"]["object"])

    s3_client = boto3.client("s3")
    # get bucket name and image name
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    photo = event["Records"][0]["s3"]["object"]["key"]
    obj = s3_client.get_object(Bucket=bucket, Key=photo)
    print(obj['Body'])
    labels = detect_labels(photo, bucket)
    print(labels)
    # get meta-data given by user during upload

    image_meta_data = s3_client.head_object(Bucket=bucket, Key=photo)

    # todo error check if the user has not specified labels
    print(image_meta_data["Metadata"]["customlabels"])
    image_meta_data_labels_list = []

    # user can specify multiplt labels. Make a comma separated list.
    image_meta_data_labels_list = (image_meta_data["Metadata"]["customlabels"]).split(",")

    # append user specified labels to labels list returned by rekognition service
    for label in image_meta_data_labels_list:
        labels.append(label)

    print("Labels detected: " + str(labels))

    # create json object to be sent to elastic search domain
    es_data_object = {
        "objectKey": photo,
        "bucket": bucket,
        "createdTimestamp": str(datetime.datetime.now().isoformat()),
        "labels": labels
    }

    print(json.dumps(es_data_object))

    # elastic search domain to hit
    es_host = 'search-photos-ohg3afluv5djy2xmrjlfubafna.us-east-1.es.amazonaws.com'
    index = 'photos'
    url = 'https://' + es_host + '/' + index + '/_doc/'

    region = 'us-east-1'  # For example, us-west-1
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    headers = {"Content-Type": "application/json"}

    # print(es.get(index="photos", doc_type="_doc", id="5"))

    r = requests.post(url, auth=awsauth, headers=headers, data=json.dumps(es_data_object))
    print(r)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
