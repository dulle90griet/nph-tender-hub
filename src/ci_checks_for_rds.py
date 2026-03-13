import json
import socket
import psycopg
import boto3
from getpass import getpass


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
        res, detail = "SocketError", str(e)
    
    rds_sock.close()
    return {"result": res, "detail": detail}


def check_rds_psql_select(psql_conn):
    try:
        with psql_conn.cursor() as cur:
            cur.execute("SELECT 1 AS test")

            result = cur.fetchall()

            if result == [(1,),]:
                res, detail = "Success", None
            else:
                res, detail = "Error", "Query executed but received unexpected response"
    
    except psycopg.Error as e:
        res, detail = type(e).__name__, str(e)
    
    psql_conn.close()
    return {"result": res, "detail": detail}


def lambda_handler(event, context):
    secrets_manager = boto3.client("secretsmanager")
    rds_secret = secrets_manager.get_secret_value(SecretId=event['RDS_login_secret'])
    rds_secret_json = json.loads(rds_secret['SecretString'])

    results = {}

    rds_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port_res = check_rds_port_responsive(
        rds_sock,
        rds_secret_json['host'],
        rds_secret_json['port']
    )
    results["check_rds_port_responsive"] = port_res

    # for ease of testing, a keyword=value Postgres connection string is expected
    psql_conn = psycopg.connect(f"""
        host={rds_secret_json['host']}
        port={rds_secret_json['port']}
        dbname={rds_secret_json['dbname']}
        user={rds_secret_json['user']}
        password={rds_secret_json['password']}
    """)
    select_res = check_rds_psql_select(psql_conn)
    results["check_rds_psql_select"] = select_res

    return {"statusCode": 200, "body": json.dumps(results, default=str)}


if __name__ == "__main__":
    rds_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    check_rds_port_responsive(rds_sock, "127.0.0.1", 5432)

    user = input("PSQL username: ")
    pwd = getpass("PSQL password: ")

    with psycopg.connect(f"""
        host=127.0.0.1
        port=5432
        dbname=donald
        user={user}
        password={pwd}
    """) as psql_conn:
        print(check_rds_psql_select(psql_conn))
