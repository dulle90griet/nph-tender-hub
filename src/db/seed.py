import argparse
import json
import boto3
import psycopg
from psycopg.sql import SQL, Identifier


def seed_job_title(psql_conn):
    with psql_conn.cursor() as cur:
        cur.execute(SQL("""
            INSERT INTO job_title
                (department, title, default_ft_weekly_hours,
                default_lunch_break_hours, hourly_rate_gbp,
                default_annual_holiday_days,
                default_annual_training_days,
                default_annual_sick_days)
            VALUES
                ('Occupational Health Advisers', 'Occupational Health Nurse', 37.5, 0.8, 99.27, 33, 10, 3)
                ,('Occupational Health Screening Nurses & Technicians', 'Occupational Health Technician (Onsite/Offsite)', 37.5, 0.8, 12.13, 33, 10, 3)
                ,('Travel Nurses', 'Travel Nurse', 37.5, 0.8, 34.56, 33, 10, 3)
                ,('Doctors', 'Occupational Health Physician', 52.5, 0.8, 23.27, 33, 10, 2)
                ,('Doctors', 'Associate', 52.5, 0.8, 86.29, 33, 10, 2)
                ,('Admin Team', 'Managing Director', 37.5, 0, 72.27, 33, 10, 3)
                ,('Admin Team', 'Operations Manager', 37.5, 0, 72.27, 33, 10, 3)
                ,('Admin Team', 'Finance Manager', 37.5, 0, 72.27, 33, 10, 3)
                ,('Admin Team', 'Sales and Marketing Manager', 37.5, 0, 72.27, 33, 10, 3)
                ,('Admin Team', 'Cleaner', 37.5, 0, 72.27, 33, 10, 3)
                ,('Admin Team', 'Business Support Administrator', 37.5, 0, 72.27, 33, 10, 3)
                ,('Admin Team', 'Specialist Administrator', 37.5, 0, 72.27, 33, 10, 3)
                ,('Admin Team', 'Operations Controller', 37.5, 0, 72.27, 33, 10, 3)
                ,('Admin Team', 'Senior Nurse', 37.5, 0, 72.27, 33, 10, 3)
        """))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get RDS connection secret name")
    parser.add_argument("--rds-secret", help="The name or ARN of the SSM secret to fetch")
    args = parser.parse_args()
    rds_secret_name = args.rds_secret

    # Logic to fetch RDS connection details using SSM Secret
    # TO BE MODULARIZED
    secrets_manager = boto3.client("secretsmanager")
    rds_secret = secrets_manager.get_secret_value(SecretId=rds_secret_name)
    rds_secret_json = json.loads(rds_secret["SecretString"])
    rds_user_secret = secrets_manager.get_secret_value(
        SecretId=rds_secret_json["user_secret"]
    )
    rds_user_secret_json = json.loads(rds_user_secret["SecretString"])

    config = {
        "host": rds_secret_json["host"],
        "port": rds_secret_json["port"],
        "dbname": rds_secret_json["dbname"],
        "user": rds_secret_json["username"],
        "password": rds_secret_json["password"],
    }

    conn_info = " ".join(f"{key}={value}" for key, value in config.items())
    with psycopg.connect(conn_info) as conn:
        seed_job_title(conn)
