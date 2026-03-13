import os
import json
import pytest
import socket
import psycopg
import boto3
from moto import mock_aws
from unittest.mock import patch, Mock, MagicMock
from src.ci_checks_for_rds import check_rds_port_responsive, check_rds_psql_select, lambda_handler


@pytest.fixture(scope="function")
def mock_rds_sock():
    mock_sock = Mock()
    mock_sock.connect_ex = Mock(return_value=0)
    mock_sock.close = Mock()
    return mock_sock


@pytest.fixture(scope="function")
def mock_psql_conn():
    mock_conn = Mock()
    mock_cursor = Mock()

    mock_cursor.fetchall = Mock(return_value=[(1,)])
    mock_cursor.__enter__ = Mock(return_value=mock_cursor)
    mock_cursor.__exit__ = Mock(return_value=None)

    mock_conn.cursor = Mock(return_value=mock_cursor)

    return mock_conn


error_selection = [
    psycopg.InterfaceError,
    psycopg.DataError,
    psycopg.OperationalError,
    psycopg.IntegrityError,
    psycopg.InternalError,
    psycopg.ProgrammingError,
    psycopg.NotSupportedError
]


def raise_error(error_type: int):
    def wrapper(*args, **kwargs):
        msg = "Test error"

        raise error_selection[error_type](msg)
    
    return wrapper


class TestRDSPortReponsivenessChecks:
    """Unit tests for the check_rds_port_responsive() function."""

    def test_connect_ex_invoked_with_expected_host_and_port(self, mock_rds_sock):
        check_rds_port_responsive(mock_rds_sock, "expected.host.name", 5432)
        mock_rds_sock.connect_ex.assert_called_with(("expected.host.name", 5432))

        check_rds_port_responsive(mock_rds_sock, "another.expected.host", 1)
        mock_rds_sock.connect_ex.assert_called_with(("another.expected.host", 1))

    
    def test_success_returns_success(self, mock_rds_sock):
        expected = {"result": "Success", "detail": None}
        response = check_rds_port_responsive(mock_rds_sock, "host", 1234)
        assert response == expected


    def test_connection_error_returns_detail(self, mock_rds_sock):
        mock_rds_sock.connect_ex.return_value = 642
        expected = {"result": "ConnectionError", "detail": 642}
        response = check_rds_port_responsive(mock_rds_sock, "host", 1234)
        assert response == expected

        mock_rds_sock.connect_ex.return_value = 404
        expected = {"result": "ConnectionError", "detail": 404}
        response = check_rds_port_responsive(mock_rds_sock, "host", 1234)
        assert response == expected


    def test_socket_timeout_returns_timeout(self, mock_rds_sock):
        mock_rds_sock.connect_ex.side_effect=socket.timeout("Test timeout")
        expected = {"result": "Timeout", "detail": None}
        response = check_rds_port_responsive(mock_rds_sock, "host", 1234)
        assert response == expected


    def test_socket_error_returns_detail(self, mock_rds_sock):
        mock_rds_sock.connect_ex.side_effect=socket.error("Test error")
        expected = {"result": "SocketError", "detail": OSError("Test error")}
        response = check_rds_port_responsive(mock_rds_sock, "host", 1234)
        assert response['result'] == expected['result']
        assert str(response['detail']) == str(expected['detail'])

        mock_rds_sock.connect_ex.side_effect=socket.error("Brzezinski incident")
        expected = {"result": "SocketError", "detail": OSError("Brzezinski incident")}
        response = check_rds_port_responsive(mock_rds_sock, "host", 1234)
        assert response['result'] == expected['result']
        assert str(response['detail']) == str(expected['detail'])


    def test_socket_closed_after_success(self, mock_rds_sock):
        check_rds_port_responsive(mock_rds_sock, "host", 1234)
        mock_rds_sock.close.assert_called_once()


    def test_socket_closed_after_connection_failure(self, mock_rds_sock):
        mock_rds_sock.connect_ex.return_value = 111

        check_rds_port_responsive(mock_rds_sock, "host", 1234)
        mock_rds_sock.close.assert_called_once()
    

    def test_socket_closed_after_socket_timeout(self, mock_rds_sock):
        mock_rds_sock.connect_ex.side_effect=socket.timeout("Test timeout")

        check_rds_port_responsive(mock_rds_sock, "host", 1234)
        mock_rds_sock.close.assert_called_once()

    
    def test_socket_closed_after_socket_error(self, mock_rds_sock):
        mock_rds_sock.connect_ex.side_effect=socket.error("Test error")

        check_rds_port_responsive(mock_rds_sock, "host", 1234)
        mock_rds_sock.close.assert_called_once()


class TestRDSPSQLSelectChecks:
    """Unit tests for the check_rds_psql_select() function."""

    def test_cursor_execute_invoked_with_select_statement(self, mock_psql_conn):
        mock_cursor = Mock()
        mock_cursor.execute = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_psql_conn.cursor = Mock(return_value=mock_cursor)

        check_rds_psql_select(mock_psql_conn)
        mock_cursor.execute.assert_called_once()
        assert mock_cursor.execute.call_args.args[0][:7] == "SELECT "


    def test_success_returns_success(self, mock_psql_conn):
        expected = {"result": "Success", "detail": None}
        response = check_rds_psql_select(mock_psql_conn)
        assert response == expected
    
    
    def test_unexpected_response_returns_error(self, mock_psql_conn):
        mock_cursor = Mock()
        mock_cursor.fetchall = Mock(return_value=[("An unexpected value",)])
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_psql_conn.cursor = Mock(return_value=mock_cursor)

        expected = {"result": "Error", "detail": "Query executed but received unexpected response"}
                    
        response = check_rds_psql_select(mock_psql_conn)
        assert response == expected

        mock_cursor.fetchall = Mock(return_value=[(1,), (2,), (3,)])
        response = check_rds_psql_select(mock_psql_conn)
        assert response == expected


    def test_psycopg_error_returns_detail(self, mock_psql_conn):
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_psql_conn.cursor = Mock(return_value=mock_cursor)

        for error_i in range(7):
            expected = {
                "result": type(error_selection[error_i]()).__name__,
                "detail": "Test error"
            }
            mock_cursor.execute = Mock(side_effect=raise_error(error_i))
            response = check_rds_psql_select(mock_psql_conn)
            assert response == expected


    def test_connection_closed_after_success(self, mock_psql_conn):
        check_rds_psql_select(mock_psql_conn)
        mock_psql_conn.close.assert_called_once()


    def test_connection_closed_after_unexpected_response(self, mock_psql_conn):
        mock_cursor = Mock()
        mock_cursor.fetchall = Mock(return_value=[("An unexpected value",)])
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_psql_conn.cursor = Mock(return_value=mock_cursor)

        check_rds_psql_select(mock_psql_conn)
        mock_psql_conn.close.assert_called_once()

        mock_cursor.fetchall = Mock(return_value=[(1,), (2,), (3,)])

        check_rds_psql_select(mock_psql_conn)
        assert mock_psql_conn.close.call_count == 2
    

    def test_connection_closed_after_psycopg_error(self, mock_psql_conn):
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_psql_conn.cursor = Mock(return_value=mock_cursor)

        for error_i in range(7):
            mock_cursor.execute = Mock(side_effect=raise_error(error_i))
            check_rds_psql_select(mock_psql_conn)
            assert mock_psql_conn.close.call_count == error_i + 1


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@pytest.fixture
def sm_client(aws_credentials):
    with mock_aws():
        secrets_manager = boto3.client("secretsmanager")
        yield secrets_manager


class TestRDSChecksLambdaHandler:
    """Unit tests for the Lambda handler."""

    @patch("src.ci_checks_for_rds.psycopg.connect")
    @patch("src.ci_checks_for_rds.boto3.client")
    @patch("src.ci_checks_for_rds.check_rds_port_responsive")
    def test_get_secret_value_called_with_event_value(
        self,
        mock_check_rds_port_responsive,
        mock_boto3_client,
        mock_psycopg_connect
    ):
        test_secret_json = {
            "host": "127.0.0.1",
            "port": 5432,
            "dbname": "testname",
            "user": "testuser",
            "password": "testpassword"
        }
        test_secret = {"SecretString": json.dumps(test_secret_json)}
        
        mock_sm_client = Mock()
        mock_sm_client.get_secret_value = Mock(return_value=test_secret)
        mock_boto3_client.return_value = mock_sm_client

        test_event = {"RDS_login_secret": "test_secret"}
        lambda_handler(test_event, object())
        assert "test_secret" in [
            mock_sm_client.get_secret_value.call_args.args[0:1],
            mock_sm_client.get_secret_value.call_args.kwargs.get('SecretId')
        ]


    @patch("src.ci_checks_for_rds.psycopg.connect")
    @patch("src.ci_checks_for_rds.boto3.client")
    @patch("src.ci_checks_for_rds.check_rds_port_responsive")
    def test_rds_port_checks_called_with_secret_values(
        self,
        mock_check_rds_port_responsive,
        mock_boto3_client,
        mock_psycopg_connect
    ):
        test_event = {"RDS_login_secret": "test_secret"}
        test_secret_json = {
            "host": "127.0.0.1",
            "port": 5432,
            "dbname": "testname",
            "user": "testuser",
            "password": "testpassword"
        }
        test_secret = {"SecretString": json.dumps(test_secret_json)}

        mock_sm_client = Mock()
        mock_sm_client.get_secret_value = Mock(return_value=test_secret)
        mock_boto3_client.return_value = mock_sm_client

        lambda_handler(test_event, object())

        assert mock_check_rds_port_responsive.call_args.args[1:3] == (
            "127.0.0.1",
            5432
        )


    @patch("src.ci_checks_for_rds.psycopg.connect")
    @patch("src.ci_checks_for_rds.boto3.client")
    @patch("src.ci_checks_for_rds.check_rds_port_responsive")
    def test_psycopg_connect_called_with_secret_values(
        self,
        mock_check_rds_port_responsive,
        mock_boto3_client,
        mock_psycopg_connect
    ):
        test_event = {"RDS_login_secret": "test_secret"}
        test_secret_json = {
            "host": "127.0.0.1",
            "port": 5432,
            "dbname": "testname",
            "user": "testuser",
            "password": "testpassword"
        }
        test_secret = {"SecretString": json.dumps(test_secret_json)}

        mock_sm_client = Mock()
        mock_sm_client.get_secret_value = Mock(return_value=test_secret)
        mock_boto3_client.return_value = mock_sm_client

        lambda_handler(test_event, object())

        mock_psycopg_connect.assert_called_once()
        connection_string = mock_psycopg_connect.call_args.args[0]
        connection_values = {
            key: value for key, value in
            [pair.split("=") for pair in connection_string.split()]
        }
        assert connection_values['host'] == "127.0.0.1"
        assert int(connection_values['port']) == 5432
        assert connection_values['dbname'] == "testname"
        assert connection_values['user'] == "testuser"
        assert connection_values['password'] == "testpassword"


    def test_psql_select_checks_called_with_expected_connection(self):
        pass
