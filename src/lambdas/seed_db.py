import logging
import json
import boto3
import psycopg
# from psycopg.sql import SQL, Identifier


logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)


def initialize_database(psql_conn):
    with psql_conn.cursor() as cur:
        initialize_database_sql = """
            DROP TABLE IF EXISTS "job_title";

            CREATE TABLE "job_title" (
                "id" SERIAL PRIMARY KEY NOT NULL
                ,"department" varchar(50) NOT NULL
                ,"title" varchar(50) NOT NULL
                ,"default_ft_weekly_hours" decimal(3,1) NOT NULL
                ,"default_lunch_break_hours" decimal(2,1) NOT NULL
                ,"hourly_rate_gbp" decimal(7,2) NOT NULL
                ,"default_annual_holiday_days" decimal(3,1)
                ,"default_annual_training_days" decimal(3,1)
                ,"default_annual_sick_days" decimal(3,1)
            );
        """
        cur.execute(initialize_database_sql)

        logger.info("Results of initialization:")
        for record in cur:
            logger.info(str(record))


def seed_job_title(psql_conn):
    with psql_conn.cursor() as cur:
        seed_job_title_sql = """
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
        """
        cur.execute(seed_job_title_sql)

        logger.info("Results of job_title table seed:")
        for record in cur:
            logger.info(str(record))


def lambda_handler(event, context):
    # Logic to fetch RDS connection details using SSM Secret
    # TO BE MODULARIZED
    secrets_manager = boto3.client("secretsmanager")
    logger.info("Fetching RDS login secret")
    rds_secret = secrets_manager.get_secret_value(SecretId=event["RDS_login_secret"])
    rds_secret_json = json.loads(rds_secret["SecretString"])
    logger.info("Fetching RDS master user secret")
    rds_user_secret = secrets_manager.get_secret_value(
        SecretId=rds_secret_json["user_secret"]
    )
    rds_user_secret_json = json.loads(rds_user_secret["SecretString"])

    config = {
        "host": rds_secret_json["host"],
        "port": rds_secret_json["port"],
        "dbname": rds_secret_json["dbname"],
        "user": rds_user_secret_json["username"],
        "password": rds_user_secret_json["password"],
    }

    conn_info = " ".join(f"{key}={value}" for key, value in config.items())
    with psycopg.connect(conn_info) as conn:
        logger.info("(Re-)initializing database")
        initialize_database(conn)
        logger.info("Seeding job_title table")
        seed_job_title(conn)

    return {"statusCode": 200}
