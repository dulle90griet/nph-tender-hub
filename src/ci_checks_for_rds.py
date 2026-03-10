import socket


def check_rds_port_responsive(rds_sock, host, port):
    try:
        rds_sock.settimeout(5)

        result = rds_sock.connect_ex((host, port))

        if result == 0:
            print(f"Successfully connected to {host}:{port}")
            res, detail = "Success", None
        else:
            print(f"Failed to connect to {host}:{port} (Error code: {result})")
            res, detail = "ConnectionError", result
    
    except socket.timeout:
        print(f"Connection to {host}:{port} timed out")
        res, detail = "Timeout", None

    except socket.error as e:
        print(f"Socket error: {e}")
        res, detail = "SocketError", e
    
    rds_sock.close()
    return {"result": res, "detail": detail}


if __name__ == "__main__":
    rds_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    check_rds_port_responsive(rds_sock, "127.0.0.1", 9999)
