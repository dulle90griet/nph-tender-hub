import json
import os, boto3


def destroy_budibase_instance(client):
    return client.update_service(
        cluster = os.environ.get("TARGET_CLUSTER_NAME"),
        service = os.environ.get("TARGET_SERVICE_NAME"),
        desiredCount = 0
    )


def lambda_handler(event, service):
    ecs_client = boto3.client("ecs")

    result = destroy_budibase_instance(ecs_client)

    return {
        "statusCode": 200,
        "body": json.dumps(result)
    }
