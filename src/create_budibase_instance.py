import os, boto3


def create_budibase_instance(client):
    client.update_service(
        cluster = os.environ.get("TARGET_CLUSTER_NAME"),
        service = os.environ.get("TARGET_SERVICE_NAME"),
        desiredCount = 1
    )


def lambda_handler(event, context):
    pass
