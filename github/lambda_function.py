import os
import json
import urllib3
from urllib.parse import urlparse

aws_session_token = os.environ.get("AWS_SESSION_TOKEN")


def get_github_token():
    http = urllib3.PoolManager()
    url = "http://localhost:2773/secretsmanager/get?secretId=prod%2Fshrey-portfolio&region=ap-south-1"
    print(url)
    res = http.request("GET", url, headers={"X-Aws-Parameters-Secrets-Token": aws_session_token})

    secrets = json.loads(json.loads(res.data.decode("utf-8"))["SecretString"])

    return secrets["GITHUB_TOKEN"]


def lambda_handler(event, context):
    print(event)

    api_response = {
        "statusCode": 405,
        "body": json.dumps({"error": "Method Not Allowed."}),
    }

    if event.get("httpMethod", "") == "OPTIONS":
        api_response = {
            "statusCode": 200,
            "body": "",
        }
    elif event.get("httpMethod", "") == "GET":
        # setup defaults
        query_github = True
        api_response = {
            "statusCode": 400,
            "body": json.dumps({"error": "Bad Request."}),
        }

        # check for where the request is originating from
        # all requests from a browser have a referrer and origin set in the event
        origin_url = event.get("headers", {}).get("origin", "")
        try:
            origin_url = urlparse(origin_url)

            if "shreydabhi.dev" not in origin_url.hostname and "localhost" not in origin_url.hostname:
                api_response = {"statusCode": 403, "body": json.dumps({"error": "Forbidden."})}

                query_github = False
        except Exception as e:
            print(e)
            query_github = False

        # only run the GitHub query if it is a good request
        if query_github is True:
            payload = json.dumps(
                {
                    "query": """{
                        repo1: repository(name: "bsedata", owner: "sdabhi23") {
                            openGraphImageUrl
                            url
                            nameWithOwner
                        }

                        repo2: repository(name: "Twitter-Clone", owner: "sdabhi23") {
                            openGraphImageUrl
                            url
                            nameWithOwner
                        }

                        repo3: repository(name: "monaco-json-viewer", owner: "sdabhi23") {
                            openGraphImageUrl
                            url
                            nameWithOwner
                        }
                      }"""
                }
            ).encode("utf-8")

            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {get_github_token()}"}

            try:
                http = urllib3.PoolManager()
                res = http.request("POST", "https://api.github.com/graphql", body=payload, headers=headers)
                api_response = {
                    "statusCode": 200,
                    "body": res.data.decode("utf-8"),
                }
            except Exception as e:
                print(e)
                api_response = {
                    "statusCode": 500,
                    "body": json.dumps({"error": "Error while querying GitHub."}),
                }

    # none of the responses are base64 encoded
    # but this stupid flag is required by the lambda proxy integration
    # so always set this to false
    api_response["isBase64Encoded"] = False

    # temporary hack to enable CORS
    api_response["headers"] = {
        "Access-Control-Allow-Origin": "https://shreydabhi.dev",
        "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    }

    return api_response
