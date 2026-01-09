import os, pytest, boto3, time
from pprint import pprint
from moto import mock_aws
from unittest.mock import patch
from src.destroy_budibase_instance import destroy_budibase_instance


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
        serviceName = os.environ["TARGET_SERVICE_NAME"],
        desiredCount = 1
    )

    # For some reason, setting desiredCount on create currently creates
    # a pending service in moto; setting on update creates a running service
    ecs_client.update_service(
        cluster = os.environ["TARGET_CLUSTER_NAME"],
        service = os.environ["TARGET_SERVICE_NAME"],
        desiredCount = 1
    )
    
    yield ecs_client


class TestCreateBudibaseInstanceFunction:
    """ Unit tests for the create_budibase_instance() function. """

    def test_service_desired_count_set_to_0(self, ecs_with_cluster):
        destroy_budibase_instance(ecs_with_cluster)
        result = ecs_with_cluster.describe_services(
            cluster = os.environ["TARGET_CLUSTER_NAME"],
            services = [os.environ["TARGET_SERVICE_NAME"]]
        )
        assert (result["services"][0]["desiredCount"] == 0
                and result["services"][0]["pendingCount"] == 0)


    def test_running_count_decreases_from_1_to_0(self, ecs_with_cluster):
        result = ecs_with_cluster.describe_services(
            cluster = os.environ["TARGET_CLUSTER_NAME"],
            services = [os.environ["TARGET_SERVICE_NAME"]]
        )
        assert (result["services"][0]["desiredCount"] == 1
                or result["services"][0]["pendingCount"] == 1)
        destroy_budibase_instance(ecs_with_cluster)

        result = ecs_with_cluster.describe_services(
            cluster = os.environ["TARGET_CLUSTER_NAME"],
            services = [os.environ["TARGET_SERVICE_NAME"]]
        )
        assert (result["services"][0]["desiredCount"] == 0
                and result["services"][0]["pendingCount"] == 0)