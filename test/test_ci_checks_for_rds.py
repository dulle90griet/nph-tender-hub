import pytest
import socket
from unittest.mock import patch, Mock
from src.ci_checks_for_rds import check_rds_port_responsive


@pytest.fixture(scope="function")
def mock_rds_sock():
    mock_sock = Mock()
    mock_sock.connect_ex = Mock(return_value=0)
    mock_sock.close = Mock()
    return mock_sock


class TestRDSPortReponsivenessChecks:
    def test_connect_ex_invoked_with_expected_host_and_port(self, mock_rds_sock):
        check_rds_port_responsive(mock_rds_sock, "expected.host.name", 5432)
        mock_rds_sock.connect_ex.assert_called_with(("expected.host.name", 5432))

        check_rds_port_responsive(mock_rds_sock, "another.expected.host", 1)
        mock_rds_sock.connect_ex.assert_called_with(("another.expected.host", 1))


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
