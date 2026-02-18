import json
import os
import boto3


def create_budibase_instance(client):
    return client.update_service(
        cluster=os.environ.get("TARGET_CLUSTER_NAME"),
        service=os.environ.get("TARGET_SERVICE_NAME"),
        desiredCount=1,
    )


def lambda_handler(event, context):
    ecs_client = boto3.client("ecs")

    result = create_budibase_instance(ecs_client)

    print("A trivial change")

    return {"statusCode": 200, "body": json.dumps(result, default=str)}
