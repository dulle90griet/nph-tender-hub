import os, pytest, boto3, time
from pprint import pprint
from moto import mock_aws
from src.create_budibase_instance import create_budibase_instance


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@pytest.fixture(scope="module")
def env_vars():
    os.environ["TARGET_CLUSTER_NAME"] = "test-cluster"
    os.environ["TARGET_SERVICE_NAME"] = "test-service"


@pytest.fixture
def ecs_client(aws_credentials, env_vars):
    with mock_aws():
        ecs = boto3.client("ecs")
        yield ecs


@pytest.fixture(scope="function")
def ecs_with_cluster(ecs_client):
    ecs_client.create_cluster(
        clusterName = os.environ["TARGET_CLUSTER_NAME"]
    )
    ecs_client.create_service(
        cluster = os.environ["TARGET_CLUSTER_NAME"],
        serviceName = os.environ["TARGET_SERVICE_NAME"]
    )
    ecs_client.update_service(
        cluster = os.environ["TARGET_CLUSTER_NAME"],
        service = os.environ["TARGET_SERVICE_NAME"],
        desiredCount = 0,
        forceNewDeployment = True
    )
    time.sleep(1)
    yield ecs_client


def test_service_desired_count_set_to_1(ecs_with_cluster):
    create_budibase_instance(ecs_with_cluster)
    result = ecs_with_cluster.describe_services(
        cluster = os.environ["TARGET_CLUSTER_NAME"],
        services = [os.environ["TARGET_SERVICE_NAME"]]
    )
    assert result["services"][0]["desiredCount"] == 1


def test_deployments_increase_from_0_to_1(ecs_with_cluster):
    result = ecs_with_cluster.describe_services(
        cluster = os.environ["TARGET_CLUSTER_NAME"],
        services = [os.environ["TARGET_SERVICE_NAME"]]
    )
    assert result["services"][0]["runningCount"] == 0

    create_budibase_instance(ecs_with_cluster)

    result = ecs_with_cluster.describe_services(
        cluster = os.environ["TARGET_CLUSTER_NAME"],
        services = [os.environ["TARGET_SERVICE_NAME"]]
    )
    assert result["services"][0]["runningCount"] == 1
