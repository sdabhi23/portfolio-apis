import os
import json
import urllib3
from urllib.parse import urlparse

aws_session_token = os.environ.get("AWS_SESSION_TOKEN")


def get_mailjet_creds():
    http = urllib3.PoolManager()
    url = "http://localhost:2773/secretsmanager/get?secretId=prod%2Fshrey-portfolio&region=ap-south-1"
    print(url)
    res = http.request("GET", url, headers={"X-Aws-Parameters-Secrets-Token": aws_session_token})

    secrets = json.loads(json.loads(res.data.decode("utf-8"))["SecretString"])

    return secrets["MJ_APIKEY_PUBLIC"], secrets["MJ_APIKEY_PRIVATE"]


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
    elif event.get("httpMethod", "") == "POST":
        # setup defaults
        send_email = True
        api_response = {
            "statusCode": 400,
            "body": json.dumps({"error": "Bad Request."}),
        }

        # check for where the request is originating from
        # all requests from a browser have a referrer and origin set in the event
        origin_url = event.get("headers", {}).get("origin", "")
        print(origin_url)

        try:
            origin_url = urlparse(origin_url)

            if "shreydabhi.dev" not in origin_url.hostname and "localhost" not in origin_url.hostname:
                api_response = {"statusCode": 403, "body": json.dumps({"error": "Forbidden."})}

                send_email = False
        except Exception as e:
            print(e)
            send_email = False

        request_body = json.loads(event["body"])

        if "name" not in request_body.keys():
            api_response = {
                "statusCode": 400,
                "body": json.dumps({"error": "Bad Request. Required values not found."}),
            }
            send_email = False

        # only sned the email if it is a good request
        if send_email is True:
            mailjet_public_key, mailjet_private_key = get_mailjet_creds()

            payload = json.dumps(
                {
                    "Globals": {
                        "From": {"Email": "", "Name": "Portfolio Email User"},
                        "Subject": "Someone is trying to contact you!",
                    },
                    "Messages": [
                        {
                            "To": [{"Email": "", "Name": "Shrey"}],
                            "TextPart": f"Name: {request_body['name']}\nEmail ID: {request_body['email']}\nPurpose: {request_body['purpose']}\nMessage: {request_body['message']}",
                        }
                    ],
                }
            )

            try:
                http = urllib3.PoolManager()
                headers = urllib3.make_headers(basic_auth=f"{mailjet_public_key}:{mailjet_private_key}")
                res = http.request("POST", "https://api.mailjet.com/v3.1/send", headers=headers, body=payload)
                mailjet_response = json.loads(res.data.decode("utf-8"))
                if mailjet_response["Messages"][0]["Status"] == "success":
                    api_response = {"statusCode": 200, "body": json.dumps(mailjet_response)}
                else:
                    api_response = {"statusCode": 500, "body": json.dumps(mailjet_response)}
            except Exception as e:
                print(e)
                api_response = {
                    "statusCode": 500,
                    "body": json.dumps({"error": "Error while sending email via MailJet."}),
                }

    # none of the responses are base64 encoded
    # but this stupid flag is required by the lambda proxy integration
    # so always set this to false
    api_response["isBase64Encoded"] = False

    # temporary hack to enable CORS
    api_response["headers"] = {
        "Access-Control-Allow-Origin": "https://shreydabhi.dev",
        "Access-Control-Allow-Methods": "POST,HEAD,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    }

    return api_response
