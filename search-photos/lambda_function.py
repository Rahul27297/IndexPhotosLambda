import json
import requests
import boto3
from requests_aws4auth import AWS4Auth

def lambda_handler(event, context):
    print(event)
    print(event["queryStringParameters"]["q"])

    lex_client = boto3.client('lex-runtime')
    lex_response = lex_client.post_text(
        botName='photoalbum',
        botAlias='photoalbum',
        userId='user1',
        inputText=event["queryStringParameters"]["q"],
    )

    print(lex_response)

    slots = lex_response["slots"]
    keywords = slots["keywords"]
    keywords_ = slots["keywords_"]
    print(slots)

    es_host = 'search-photos-ohg3afluv5djy2xmrjlfubafna.us-east-1.es.amazonaws.com'
    index = 'photos'
    url = 'https://' + es_host + '/' + index + '/_search/'

    region = 'us-east-1'  # For example, us-west-1
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    headers = {"Content-Type": "application/json"}

    if keywords is not None:
        label_value = keywords

    if keywords_ is not None:
        label_value += " AND " + keywords_

    query = {
        "query": {
            "match": {"labels": label_value}
          }
    }
    print(json.dumps(query))
    r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
    r_dict = json.loads(r.text)
    print("Rahul")
    print(r_dict)
    result_list = r_dict["hits"]["hits"]
    image_url_list = []

    response = {}
    response["results"] = []
    if result_list is not None:
        for result in result_list:
            response_object = {}
            s3_url = "https://" + result["_source"]["bucket"] + ".s3.amazonaws.com/" + result["_source"]["objectKey"]
            response_object["url"] = s3_url
            response_object["labels"] = result["_source"]["labels"]
            response["results"].append(response_object)

    print(response)

    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
        'body': json.dumps(response)
    }
