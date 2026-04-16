import random
from decimal import Decimal
import logging
import json
import boto3
import psycopg
# from psycopg.sql import SQL, Identifier


logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)


class ConsumableGenerator:
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


class ServiceGenerator:
    _pillars = [
        "Attendance Management",
        "Health Promotion",
        "Clinical Services",
        "Pathology",
        "Travel Health",
        "Unknown Pillar Name",
    ]

    _categories_by_pillar = {
        "Attendance Management": [
            "Onsite Service Lines (Client)",
            "Victory House",
            "Attendance Management",
        ],
        "Health Promotion": ["Private GP", "Wellbeing"],
        "Clinical Services": [
            "Doctor Medicals",
            "Nurse Medicals",
            "Physiotherapy",
            "Counselling",
        ],
        "Pathology": ["Pathology Tests"],
        "Travel Health": ["Vaccinations", "Travel Risk Assessments"],
        "Unknown Pillar Name": [
            "Doctor Medicals",
            "Nurse Medicals",
            "Pathology Tests",
            "Vaccinations",
            "Counselling",
        ],
    }

    _roles = [
        "OH Physician",
        "OH Advisor",
        "OH Technician",
        "Clinic Nurse",
        "Private GP",
        "Specialist",
    ]
    _tests = [
        "Audiometry",
        "Spirometry",
        "ECG",
        "Vision Test",
        "Drug Screen",
        "Cholesterol Check",
        "FBC",
        "Lipid Profile",
        "LFT",
        "HbA1c",
        "PSA",
        "Vitamin D",
    ]
    _vaccines = [
        "Flu",
        "Hepatitis A",
        "Hepatitis B",
        "Typhoid",
        "Yellow Fever",
        "MMR",
        "Rabies",
    ]
    _other = [
        "Fit Note",
        "Prescription",
        "Referral Letter",
        "Ill Health Retirement",
        "Asbestos Medical",
        "HAVS Assessment",
        "Lead Medical",
        "CAA Medical",
        "Seafarer Medical",
        "Initial Assessment",
        "Follow-up Session",
        "Case Management",
        "Room Hire",
    ]

    _prefixes = ["Onsite", "Offsite", "Remote", "Private", "Corporate", "Rapid", ""]
    _suffixes = [
        "Assessment",
        "Consultation",
        "Review",
        "Session",
        "Service",
        "Test",
        "Screen",
        "",
    ]
    _durations = ["15", "20", "30", "45", "60", "90", "120"]

    _overheads = [147, 200, 220, 250, 180, 210]

    _comments = [None] * 4
    _comments += [
        "Based on numbers ordered",
        "Plus clinical time & minimum quantity",
        "Minimum order applies",
        "Includes report",
    ]

    def __init__(self, start_xero_code: int = 4000):
        self._xero = start_xero_code

    def _next_xero(self) -> int:
        code = self._xero
        self._xero += 1
        return code

    def _build_service_name(self) -> str:
        core = random.choice(self._roles + self._tests + self._vaccines + self._other)
        parts = []
        if random.random() < 0.5:
            parts.append(random.choice(self._prefixes))
        parts.append(core)
        if random.random() < 0.4:
            parts.append(random.choice(self._suffixes))
        name = " ".join(parts)
        if random.random() < 0.3:
            name += f" ({random.choice(self._durations)} mins)"
        return name

    def _price_base_for_name(self, name: str) -> float:
        if "Physician" in name or "GP" in name:
            return random.uniform(150, 450)
        if "Advisor" in name or "Nurse" in name:
            return random.uniform(80, 280)
        if "Technician" in name:
            return random.uniform(40, 180)
        if any(t in name for t in self._tests) or "Pathology" in name:
            return random.uniform(30, 500)
        if any(v in name for v in self._vaccines) or "Vaccin" in name:
            return random.uniform(25, 200)
        return random.uniform(50, 300)

    def generate_row(self, seen_names: set) -> tuple:
        pillar = random.choice(self._pillars)
        category = random.choice(self._categories_by_pillar[pillar])

        name = self._build_service_name()
        while name in seen_names:
            name = f"{self._build_service_name()} (Variant {random.randint(2, 99)})"
        seen_names.add(name)

        overhead = random.choice(self._overheads)
        profit = Decimal(str(round(random.uniform(10.0, 30.0), 2)))
        base_price = self._price_base_for_name(name)
        acceptable = Decimal(str(round(base_price, 2)))
        current = (
            acceptable * Decimal(str(round(random.uniform(0.92, 0.98), 2)))
        ).quantize(Decimal("0.01"))
        new = (
            acceptable * Decimal(str(round(random.uniform(1.02, 1.10), 2)))
        ).quantize(Decimal("0.01"))
        day_rate = (new * Decimal(random.choice(["7.5", "8.0"]))).quantize(
            Decimal("0.01")
        )
        comment = random.choice(self._comments)

        return (
            pillar,
            category,
            name,
            self._next_xero(),
            overhead,
            profit,
            acceptable,
            current,
            new,
            day_rate,
            comment,
        )
    

class OverheadCostGenerator:
    _cost_types = [
        "Facilities",
        "Technology",
        "Administrative",
        "Professional Fees",
        "Marketing",
        "Employee Benefits",
        "HR",
        "Business Development",
        "Employee Development",
    ]

    _descriptions_by_type = {
        "Facilities": [
            "Office Rent", "Utilities", "Office Cleaning", "Security Services",
            "Waste Disposal", "Pest Control", "Landscaping", "Parking Fees",
            "Climate Control", "Elevator Maintenance", "Fire Safety",
            "Access Control", "CCTV Maintenance", "First Aid Supplies",
            "Safety Equipment", "Office Furniture",
        ],
        "Technology": [
            "Internet Service", "Software Licenses", "Hardware Maintenance",
            "Equipment Rental", "Cloud Storage", "Phone Systems",
            "Website Maintenance", "Data Backup", "Cybersecurity",
            "Meeting Room Equipment", "Video Conferencing", "Project Management Tools",
            "CRM System License", "IT Support",
        ],
        "Administrative": [
            "Office Supplies", "Professional Insurance", "Travel Expenses",
            "Printing Services", "Postage and Shipping", "Bank Charges",
            "Subscriptions", "Membership Dues", "Vehicle Maintenance",
            "Fuel Costs", "Document Storage", "Shredding Services",
        ],
        "Professional Fees": [
            "Accounting Services", "Legal Services", "Consulting Fees",
            "Audit Fees", "Tax Preparation", "Translation Services",
            "Notary Services", "Architect Fees",
        ],
        "Marketing": [
            "Marketing Materials", "Digital Advertising", "SEO Services",
            "Social Media Management", "Content Creation", "Public Relations",
            "Branding", "Promotional Items",
        ],
        "Employee Benefits": [
            "Health Insurance", "Pension Contributions", "Team Building Events",
            "Employee Recognition", "Wellness Program", "Performance Bonuses",
            "Team Lunches", "Coffee and Snacks", "Fitness Subsidy",
            "Commuter Benefits", "Mobile Phone Allowance", "Home Office Stipend",
        ],
        "HR": [
            "Recruitment Costs", "Background Checks", "Temporary Staff",
            "Employee Handbook", "Compliance Training", "Diversity Programs",
            "Succession Planning", "Exit Interviews", "Reference Checks",
            "Onboarding Materials", "Employee Surveys",
        ],
        "Business Development": [
            "Client Entertainment", "Trade Show Participation", "Conference Fees",
            "Corporate Gifts", "Sponsorships", "Market Research",
            "Customer Surveys", "Networking Events",
        ],
        "Employee Development": [
            "Training Programs", "Professional Development", "Certification Fees",
            "Industry Publications", "Mentorship Program", "Coaching Sessions",
            "Leadership Training",
        ],
    }

    def generate_row(self, seen_descriptions: set) -> tuple:
        cost_type = random.choice(self._cost_types)
        available = [
            d for d in self._descriptions_by_type[cost_type]
            if d not in seen_descriptions
        ]
        if not available:
            base = random.choice(self._descriptions_by_type[cost_type])
            description = f"{base} (Variant {random.randint(2,99)})"
            while description in seen_descriptions:
                description = f"{base} (Variant {random.randint(2,99)})"
        else:
            description = random.choice(available)
        seen_descriptions.add(description)

        budget = random.randint(1000, 85000)
        budget = round(budget / 500) * 500

        return (cost_type, description, budget)


def initialize_database(psql_conn):
    with psql_conn.cursor() as cur:
        initialize_database_sql = """
            DROP TABLE IF EXISTS "job_title";
            DROP TABLE IF EXISTS "consumable";
            DROP TABLE IF EXISTS "service";
            DROP TABLE IF EXISTS "overhead_cost";

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

            CREATE TABLE "service" (
                "id" SERIAL PRIMARY KEY NOT NULL
                ,"pillar" varchar(50) NOT NULL
                ,"category" varchar(50) NOT NULL
                ,"service_name" varchar(75) NOT NULL
                ,"xero_code" int NOT NULL
                ,"overhead_recovery_on_labour_percentage" int NOT NULL
                ,"required_profit_margin_percentage" decimal(4,2) NOT NULL
                ,"acceptable_market_price_gbp" decimal(8,2) NOT NULL
                ,"our_current_hourly_price_gbp" decimal(8,2) NOT NULL
                ,"new_hourly_price_gbp" decimal(8,2)
                ,"new_day_rate_gbp" decimal(9,2)
                ,"comments" varchar(100)
            );

            CREATE TABLE "overhead_cost" {
                "id" SERIAL PRIMARY KEY NOT NULL
                ,"cost_type" varchar(30) NOT NULL
                ,"cost_description" varchar(30) NOT NULL
                ,"budgeted_spend_gbp" int NOT NULL
            };
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
        logger.info("%s rows in job_title table", len(res))
        return res


def seed_consumable(psql_conn, n: int):
    gen = ConsumableGenerator()

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

    count_consumable_sql = "SELECT COUNT(*) FROM consumable;"
    select_from_consumable_sql = "SELECT * FROM consumable LIMIT 20;"

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
            "Returning %s of %s rows in consumable table", len(res), count
        )
        return res


def seed_service(psql_conn, n: int):
    gen = ServiceGenerator(start_xero_code=5000)
    seen = set()
    rows = [gen.generate_row(seen) for _ in range(n)]

    insert_service_sql = """
        INSERT INTO service (
            pillar,
            category,
            service_name,
            xero_code,
            overhead_recovery_on_labour_percentage,
            required_profit_margin_percentage,
            acceptable_market_price_gbp,
            our_current_hourly_price_gbp,
            new_hourly_price_gbp,
            new_day_rate_gbp,
            comments
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    count_service_sql = "SELECT COUNT(*) FROM service;"
    select_service_sql = "SELECT * FROM service LIMIT 20;"

    with psql_conn.cursor() as cur:
        cur.executemany(insert_service_sql, rows)
        psql_conn.commit()

        cur.execute(count_service_sql)
        count = cur.fetchone()[0]
        cur.execute(select_service_sql)
        res = cur.fetchall()
        logger.info(
            "Returning %s of %s rows in service table", len(res), count
        )
        return res


def seed_overhead_cost(psql_conn, n: int):
    gen = OverheadCostGenerator()
    seen = set()
    rows = [gen.generate_row(seen) for _ in range(n)]

    insert_overhead_cost_sql = """
        INSERT INTO overhead_cost (cost_type, cost_description, budgeted_spend_gbp)
        VALUES (%s, %s, %s)
    """

    count_overhead_cost_sql = "SELECT COUNT(*) FROM overhead_cost;"
    select_overhead_cost_sql = "SELECT * FROM overhead_cost LIMIT 20;"

    with psql_conn.cursor() as cur:
        cur.executemany(insert_overhead_cost_sql, rows)
        psql_conn.commit()

        cur.execute(count_overhead_cost_sql)
        count = cur.fetchone()[0]
        cur.execute(select_overhead_cost_sql)
        res = cur.fetchall()
        logger.info("Returning %s of %s rows in overhead_cost table", len(res), count)
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
        results["rows_from_consumable"] = seed_consumable(conn, 75)
        logger.info("Seeding service table")
        results["rows_from_service"] = seed_service(conn, 100)
        logger.info("Seeding overhead_cost table")
        results["rows_from_overhead_cost"] = seed_overhead_cost(conn, 100)

    return {"statusCode": 200, "body": json.dumps(results, default=str)}
