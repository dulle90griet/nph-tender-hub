import random
from decimal import Decimal
import logging
import json
import boto3
import psycopg
# from psycopg.sql import SQL, Identifier


logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)


class MedicalConsumableGenerator:
    _item_templates = [
        ("Syringe", 0.15, 0.80),
        ("Needle", 0.10, 0.60),
        ("Glove", 0.08, 0.50),
        ("Mask", 0.05, 1.20),
        ("Swab", 0.04, 0.30),
        ("Dressing", 0.50, 8.00),
        ("Bandage", 0.30, 4.00),
        ("Test Strip", 0.20, 2.50),
        ("Lancet", 0.08, 0.40),
        ("Container", 0.10, 1.50),
        ("Tube", 0.15, 2.00),
        ("Wipe", 0.03, 0.25),
        ("Gown", 1.00, 12.00),
        ("Apron", 0.50, 3.00),
        ("Electrode", 0.20, 2.00),
        ("Mouthpiece", 0.30, 2.50),
        ("Speculum", 1.50, 8.00),
        ("Cannula", 0.80, 5.00),
        ("Catheter", 2.00, 20.00),
        ("Suture", 1.00, 15.00),
    ]
    _modifiers = [
        "Sterile",
        "Disposable",
        "Non-Sterile",
        "Powder-Free",
        "Latex",
        "Nitrile",
        "Vinyl",
        "Cotton",
        "Gauze",
        "Adhesive",
        "Elastic",
    ]
    _sizes = [
        "Small",
        "Medium",
        "Large",
        "Paediatric",
        "Adult",
        "Neonatal",
        "2ml",
        "5ml",
        "10ml",
        "20ml",
        "18G",
        "21G",
        "23G",
        "25G",
    ]
    _kits = [
        "Urinalysis Test Kit",
        "Blood Glucose Test Kit",
        "Cholesterol Test Kit",
        "Pregnancy Test Kit",
        "Strep A Test Kit",
        "Influenza Test Kit",
        "Drug Screening Kit",
        "Alcohol Breathalyser",
        "ECG Recording Paper",
        "Spirometry Mouthpiece",
        "Audiometry Ear Tips",
        "Doppler Ultrasound Gel",
    ]

    _suffix_components = [
        "Sticks",
        "bottles",
        "gloves",
        "paper",
        "tabs",
        "razors",
        "Cotton Wool",
        "Sterets",
        "Lancets",
        "Test Disc",
        "Test Kit",
        "paperwork",
        "mouthpiece",
        "admin time",
    ]

    def generate_name(self) -> str:
        roll = random.random()
        if roll < 0.3:
            name = f"{random.choice(self._sizes)} {random.choice(self._modifiers)} {random.choice(self._item_templates)[0]}"
        elif roll < 0.6:
            name = f"{random.choice(self._modifiers)} {random.choice(self._item_templates)[0]}"
        else:
            name = random.choice(self._kits)

        if random.random() < 0.4:
            comps = random.sample(self._suffix_components, k=random.randint(2, 4))
            if len(comps) == 2:
                suffix = f", inc. {comps[0]} and {comps[1]}"
            else:
                suffix = f", inc. {', '.join(comps[:-1])} and {comps[-1]}"
            name += suffix
        return name

    def generate_cost(self, name: str) -> Decimal:
        for item, low, high in self._item_templates:
            if item.lower() in name.lower():
                return Decimal(str(round(random.uniform(low, high), 2)))
        return Decimal(str(round(random.uniform(1.50, 45.00), 2)))


def initialize_database(psql_conn):
    with psql_conn.cursor() as cur:
        initialize_database_sql = """
            DROP TABLE IF EXISTS "job_title";
            DROP TABLE IF EXISTS "consumable";

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

            CREATE TABLE "consumable" (
                "id" SERIAL PRIMARY KEY NOT NULL
                ,"consumable_name" varchar(100) NOT NULL
                ,"default_unit_cost_gbp" decimal(6,2)
            );
        """
        cur.execute(initialize_database_sql)

        list_tables_sql = """
            SELECT * FROM pg_catalog.pg_tables
                WHERE schemaname = 'public';
        """
        cur.execute(list_tables_sql)
        res = cur.fetchall()
        logger.info("%s tables in database sent to output file", len(res))
        return res


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
                ,('Doctors', 'Occupational Health Physician', 44.5, 0.8, 23.27, 33, 10, 2)
                ,('Doctors', 'Associate', 38.0, 0.8, 86.29, 33, 10, 2)
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

        select_from_job_title_sql = """
            SELECT * FROM job_title;
        """
        cur.execute(select_from_job_title_sql)
        res = cur.fetchall()
        logger.info("%s rows in job_title table sent to output file", len(res))
        return res


def seed_consumable(psql_conn, n: int):
    gen = MedicalConsumableGenerator()

    seen = set()
    rows = []
    while len(rows) < n:
        name = gen.generate_name()
        if name in seen:
            name = f"{name} (Pack of {random.choice([10, 25, 50, 100])})"
        if name in seen:
            continue
        seen.add(name)
        cost = gen.generate_cost(name)
        rows.append((name, cost))

    count_consumable_sql = """
        SELECT COUNT(*) FROM consumable;
    """
    select_from_consumable_sql = """
        SELECT * FROM consumable;
    """

    with psql_conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO consumable (consumable_name, default_unit_cost_gbp) VALUES (%s, %s)",
            rows,
        )
        psql_conn.commit()

        cur.execute(count_consumable_sql)
        count = cur.fetchone()[0]
        cur.execute(select_from_consumable_sql)
        res = cur.fetchall()
        logger.info(
            "%s of %s rows in consumable table sent to output file", count, len(res)
        )
        return res


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

    results = {}

    conn_info = " ".join(f"{key}={value}" for key, value in config.items())
    with psycopg.connect(conn_info) as conn:
        logger.info("(Re-)initializing database")
        results["tables_in_db"] = initialize_database(conn)
        logger.info("Seeding job_title table")
        results["rows_in_job_title"] = seed_job_title(conn)
        logger.info("Seeding consumable table")
        results["rows_from_consumable"] = seed_consumable(conn, 100)

    return {"statusCode": 200, "body": json.dumps(results, default=str)}
