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
        name = " ".join(parts).strip()
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
    _types = ["Facilities", "Technology", "Administrative", "Professional Fees"]
    _types += ["Marketing", "Employee Benefits", "HR", "Business Development"]
    _stems = {
        "Facilities": [
            "Office Rent",
            "Utilities",
            "Cleaning",
            "Security",
            "Maintenance",
        ],
        "Technology": ["Software", "Hardware", "Cloud", "Licenses", "Support"],
        "Administrative": [
            "Supplies",
            "Insurance",
            "Travel",
            "Postage",
            "Subscriptions",
        ],
        "Professional Fees": ["Accounting", "Legal", "Consulting", "Audit", "Tax Prep"],
        "Marketing": ["Advertising", "SEO", "Content", "Social Media", "Events", "PR"],
        "Employee Benefits": ["Health Insurance", "Pension", "Bonuses", "Perks"],
        "HR": ["Recruitment", "Training", "Compliance", "Onboarding", "Surveys"],
        "Business Development": ["Entertainment", "Trade Shows", "Sponsorships"],
        "Employee Development": ["Courses", "Certifications", "Coaching", "Mentoring"],
    }
    _mods = ["Main", "Q1", "Q2", "Q3", "Q4", "Basic", "Premium", "Annual", "Monthly"]
    _mods += ["On‑Site", "Remote", "EU", "UK", "Global", "Extended", "Plus"]

    def generate_row(self, seen_descriptions: set) -> tuple:
        cost_type = random.choice(self._types)
        available = [d for d in self._stems[cost_type] if d not in seen_descriptions]
        if not available:
            base = random.choice(self._stems[cost_type])
            description = (
                f"{base} ({random.choice(self._mods)})"
                if random.random() < 0.5
                else f"{base} (Variant {random.randint(2, 99)})"
            )
            while description in seen_descriptions:
                description = f"{base} (Variant {random.randint(2, 99)})"
            while len(description) > 30:
                words = description.split(" ")
                words.pop(random.choice(len(words)))
                description = " ".join(words)
        else:
            description = random.choice(available)
        seen_descriptions.add(description)

        budget = random.randint(1000, 85000)
        budget = round(budget / 500) * 500

        return (cost_type, description, budget)


class LabourCostGenerator:
    _time_options = [15, 30, 45, 60, 90, 120, 180]

    def __init__(self, service_count: int, job_title_count: int):
        self.service_count = service_count
        self.job_title_count = job_title_count
        self.max_combinations = service_count * job_title_count

    def generate_row(self, seen_pairs: set) -> tuple | None:
        if len(seen_pairs) >= self.max_combinations:
            return None
        while True:
            service_id = random.randint(1, self.service_count)
            title_id = random.randint(1, self.job_title_count)
            if (service_id, title_id) not in seen_pairs:
                seen_pairs.add((service_id, title_id))
                break
        time_mins = random.choice(self._time_options)
        return (service_id, title_id, time_mins)


class DirectCostGenerator:
    def __init__(self, service_count: int, consumable_count: int):
        self.service_count = service_count
        self.consumable_count = consumable_count
        self.max_combinations = service_count * consumable_count

    def generate_row(self, seen_pairs: set) -> tuple | None:
        if len(seen_pairs) >= self.max_combinations:
            return None
        while True:
            service_id = random.randint(1, self.service_count)
            consumable_id = random.randint(1, self.consumable_count)
            if (service_id, consumable_id) not in seen_pairs:
                seen_pairs.add((service_id, consumable_id))
                break
        cost_seed = random.uniform(1, 100)
        cost_gbp = Decimal(str(round(1 + 249 * ((cost_seed - 1) / 99) ** 7.3, 2)))
        return (service_id, consumable_id, cost_gbp)


class TenderLineItemGenerator:
    def __init__(
        self,
        num_tenders: int,
        num_services: int,
        num_job_titles: int,
        min_rows_per_tender: int,
        max_rows_per_tender: int,
        valid_labour_pairs: set,
    ):
        self.num_tenders = num_tenders
        self.num_services = num_services
        self.num_job_titles = num_job_titles
        self.min_rows = min_rows_per_tender
        self.max_rows = max_rows_per_tender
        self.valid_labour_pairs = valid_labour_pairs

    def generate_rows(self) -> list:
        seen = set()
        rows = []
        for tender_id in range(1, self.num_tenders + 1):
            n_rows = random.randint(self.min_rows, self.max_rows)
            attempts = 0
            while (
                len([r for r in rows if r[0] == tender_id]) < n_rows and attempts < 100
            ):
                # Pick a valid service/title pair that references labour_cost
                if self.valid_labour_pairs:
                    service_id, title_id = random.choice(list(self.valid_labour_pairs))
                else:
                    service_id = random.randint(1, self.num_services)
                    title_id = random.randint(1, self.num_job_titles)

                if (tender_id, service_id, title_id) not in seen:
                    seen.add((tender_id, service_id, title_id))
                    quantity = random.randint(1, 20)
                    # duration = random.choice([15, 30, 45, 60, 90, 120, 150, 180])
                    override = (
                        Decimal(str(round(random.uniform(20.0, 200.0), 2)))
                        if random.random() < 0.3
                        else None
                    )
                    rows.append((tender_id, service_id, title_id, quantity, override))
                attempts += 1
        return rows


def initialize_database(psql_conn):
    with psql_conn.cursor() as cur:
        initialize_database_sql = """
            -- Dependent tables
            DROP TABLE IF EXISTS "tenders_services_job_titles";
            DROP TABLE IF EXISTS "tender";
            DROP TABLE IF EXISTS "direct_cost";
            DROP TABLE IF EXISTS "labour_cost";
            DROP TABLE IF EXISTS "job_title";

            -- Independent tables
            DROP TABLE IF EXISTS "client";
            DROP TABLE IF EXISTS "overhead_cost";
            DROP TABLE IF EXISTS "service";
            DROP TABLE IF EXISTS "consumable";
            DROP TABLE IF EXISTS "department";

            CREATE TABLE "department" (
                "id" SERIAL PRIMARY KEY NOT NULL
                ,"name" varchar(50) NOT NULL
            );

            CREATE TABLE "job_title" (
                "id" SERIAL PRIMARY KEY NOT NULL
                ,"department_id" int NOT NULL
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

            CREATE TABLE "overhead_cost" (
                "id" SERIAL PRIMARY KEY NOT NULL
                ,"cost_type" varchar(30) NOT NULL
                ,"cost_description" varchar(30) NOT NULL
                ,"budgeted_spend_gbp" int NOT NULL
            );

            CREATE TABLE "labour_cost" (
                "service_id" int NOT NULL
                ,"title_engaged_id" int NOT NULL
                ,"required_time_mins" int NOT NULL
                ,PRIMARY KEY ("service_id", "title_engaged_id")
            );

            CREATE TABLE "direct_cost" (
                "service_id" int NOT NULL
                ,"consumable_id" int NOT NULL
                ,"cost_gbp" decimal(5,2) NOT NULL
                ,PRIMARY KEY ("service_id", "consumable_id")
            );

            CREATE TABLE "client" (
                "id" SERIAL PRIMARY KEY NOT NULL
                ,"client_name" varchar(50) NOT NULL
            );

            CREATE TABLE "tender" (
                "id" SERIAL PRIMARY KEY NOT NULL
                ,"tender_title" varchar(50) NOT NULL
                ,"client_id" int NOT NULL
                ,"projected_sales_value_gbp" int NOT NULL
                ,"date_created" timestamp NOT NULL
            );

            CREATE TABLE "tenders_services_job_titles" (
                "tender_id" int NOT NULL
                ,"service_id" int NOT NULL
                ,"title_engaged_id" int NOT NULL
                ,"total_number_pa" int NOT NULL
                ,"hourly_price_override_gbp" decimal(8,2)
                ,PRIMARY KEY ("tender_id", "service_id", "title_engaged_id")
            );

            ALTER TABLE "job_title" ADD FOREIGN KEY ("department_id") REFERENCES "department" ("id");
            ALTER TABLE "job_title" ADD CONSTRAINT unique_title UNIQUE ("title");

            ALTER TABLE "service" ADD CONSTRAINT unique_slug UNIQUE("category", "service_name");

            ALTER TABLE "labour_cost" ADD FOREIGN KEY ("service_id") REFERENCES "service" ("id");
            ALTER TABLE "labour_cost" ADD FOREIGN KEY ("title_engaged_id") REFERENCES "job_title" ("id");

            ALTER TABLE "direct_cost" ADD FOREIGN KEY ("service_id") REFERENCES "service" ("id");
            ALTER TABLE "direct_cost" ADD FOREIGN KEY ("consumable_id") REFERENCES "consumable" ("id");

            ALTER TABLE "tender" ADD FOREIGN KEY ("client_id") REFERENCES "client" ("id");

            ALTER TABLE "tenders_services_job_titles" ADD FOREIGN KEY ("tender_id") REFERENCES "tender" ("id");
            ALTER TABLE "tenders_services_job_titles" ADD FOREIGN KEY ("service_id") REFERENCES "service" ("id");
            ALTER TABLE "tenders_services_job_titles" ADD FOREIGN KEY ("title_engaged_id") REFERENCES "job_title" ("id");
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


def seed_department(psql_conn):
    with psql_conn.cursor() as cur:
        seed_department_sql = """
            INSERT INTO department
                (name)
            VALUES
                ('Admin Team')
                ,('Doctors')
                ,('Travel Nurses')
                ,('Occupational Health Advisers')
                ,('Occupational Health Screening Nurses & Technicians')
        """
        cur.execute(seed_department_sql)

        select_from_department_sql = """
            SELECT * FROM department LIMIT 20;
        """
        cur.execute(select_from_department_sql)
        res = cur.fetchall()
        logger.info("%s rows in department table", len(res))
        return res


def seed_job_title(psql_conn):
    with psql_conn.cursor() as cur:
        seed_job_title_sql = """
            INSERT INTO job_title
                (department_id, title, default_ft_weekly_hours,
                default_lunch_break_hours, hourly_rate_gbp,
                default_annual_holiday_days,
                default_annual_training_days,
                default_annual_sick_days)
            VALUES
                (4, 'Occupational Health Nurse', 37.5, 0.8, 99.27, 33, 10, 3)
                ,(5, 'Occupational Health Technician (Onsite/Offsite)', 37.5, 0.8, 12.13, 33, 10, 3)
                ,(3, 'Travel Nurse', 37.5, 0.8, 34.56, 33, 10, 3)
                ,(2, 'Occupational Health Physician', 44.5, 0.8, 23.27, 33, 10, 2)
                ,(2, 'Associate', 38.0, 0.8, 86.29, 33, 10, 2)
                ,(1, 'Managing Director', 37.5, 0, 72.27, 33, 10, 3)
                ,(1, 'Operations Manager', 37.5, 0, 72.27, 33, 10, 3)
                ,(1, 'Finance Manager', 37.5, 0, 72.27, 33, 10, 3)
                ,(1, 'Sales and Marketing Manager', 37.5, 0, 72.27, 33, 10, 3)
                ,(1, 'Cleaner', 37.5, 0, 72.27, 33, 10, 3)
                ,(1, 'Business Support Administrator', 37.5, 0, 72.27, 33, 10, 3)
                ,(1, 'Specialist Administrator', 37.5, 0, 72.27, 33, 10, 3)
                ,(1, 'Operations Controller', 37.5, 0, 72.27, 33, 10, 3)
                ,(1, 'Senior Nurse', 37.5, 0, 72.27, 33, 10, 3)
        """
        cur.execute(seed_job_title_sql)

        select_from_job_title_sql = """
            SELECT * FROM job_title LIMIT 20;
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
        logger.info("Returning %s of %s rows in consumable table", len(res), count)
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
        logger.info("Returning %s of %s rows in service table", len(res), count)
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


def seed_labour_cost(psql_conn, n: int, service_count: int, job_title_count: int):
    gen = LabourCostGenerator(service_count, job_title_count)
    max_possible = service_count * job_title_count
    if n > max_possible:
        logger.warning(
            "Requested %s rows but only %s combinations exist. Generating %s rows.",
            n,
            max_possible,
            max_possible,
        )
        n = max_possible

    seen = set()
    rows = []
    for _ in range(n):
        row = gen.generate_row(seen)
        if row is None:
            break
        rows.append(row)

    insert_labour_cost_sql = """
        INSERT INTO labour_cost (service_id, title_engaged_id, required_time_mins)
        VALUES (%s, %s, %s)
    """

    count_labour_cost_sql = "SELECT COUNT(*) FROM labour_cost;"
    select_labour_cost_sql = "SELECT * FROM labour_cost LIMIT 20;"

    with psql_conn.cursor() as cur:
        cur.executemany(insert_labour_cost_sql, rows)
        psql_conn.commit()

        cur.execute(count_labour_cost_sql)
        count = cur.fetchone()[0]
        cur.execute(select_labour_cost_sql)
        res = cur.fetchall()
        logger.info(
            "%s of %s rows in labour_cost table sent to output", len(res), count
        )
        return res


def seed_direct_cost(psql_conn, n: int, service_count: int, consumable_count: int):
    gen = DirectCostGenerator(service_count, consumable_count)
    max_possible = service_count * consumable_count
    if n > max_possible:
        logger.warning(
            "Requested %s rows but only %s combinations exist. Generating %s rows.",
            n,
            max_possible,
            max_possible,
        )
        n = max_possible

    seen = set()
    rows = []
    for _ in range(n):
        row = gen.generate_row(seen)
        if row is None:
            break
        rows.append(row)

    insert_direct_cost_sql = """
        INSERT INTO direct_cost (service_id, consumable_id, cost_gbp)
        VALUES (%s, %s, %s)
    """

    count_direct_cost_sql = "SELECT COUNT(*) FROM direct_cost;"
    select_direct_cost_sql = "SELECT * FROM direct_cost LIMIT 20;"

    with psql_conn.cursor() as cur:
        cur.executemany(insert_direct_cost_sql, rows)
        psql_conn.commit()

        cur.execute(count_direct_cost_sql)
        count = cur.fetchone()[0]
        cur.execute(select_direct_cost_sql)
        res = cur.fetchall()
        logger.info(
            "%s of %s rows in direct_cost table sent to output", len(res), count
        )
        return res


def seed_client(psql_conn):
    insert_client_sql = """
        INSERT INTO client
            (client_name)
        VALUES
            ('Transport for London'),
            ('NHS Trust Manchester'),
            ('Midlands Development Co'),
            ('Glasgow City Council'),
            ('Yorkshire Properties Ltd'),
            ('Liverpool City Council'),
            ('West Country Homes'),
            ('Scottish Heritage Trust'),
            ('Welsh Sports Authority'),
            ('North East Development'),
            ('South Yorkshire Transport'),
            ('East Midlands Retail Group'),
            ('Maritime Services UK'),
            ('Ministry of Defence'),
            ('University of Leicester'),
            ('Brighton & Hove Council'),
            ('Automotive Industries Ltd'),
            ('Humber Development Co'),
            ('Potteries Development'),
            ('Network Rail Midlands'),
            ('Thames Valley Properties'),
            ('Logistics Solutions UK'),
            ('Lancashire County Council'),
            ('Swansea Bay Development'),
            ('Yorkshire Retail Group'),
            ('North East Marine Ltd'),
            ('Airport Holdings Ltd'),
            ('West Midlands Education'),
            ('South West Coastal Agency'),
            ('York Historical Trust'),
            ('Greater Manchester Council'),
            ('Eastern Distribution Co'),
            ('Stockport Borough Council'),
            ('Brighton Pier Company'),
            ('Midlands Manufacturing'),
            ('Tech Infrastructure Ltd');
    """

    count_client_sql = "SELECT COUNT(*) FROM client;"
    select_client_sql = "SELECT * FROM client LIMIT 20;"

    with psql_conn.cursor() as cur:
        cur.execute(insert_client_sql)
        psql_conn.commit()

        cur.execute(count_client_sql)
        count = cur.fetchone()[0]
        cur.execute(select_client_sql)
        res = cur.fetchall()
        logger.info("%s of %s rows in client table sent to output", len(res), count)
        return res


def seed_tender(psql_conn):
    insert_tender_sql = """
        INSERT INTO tender
            (tender_title, client_id, projected_sales_value_gbp, date_created)
        VALUES
            ('London Bridge Renovation', 1, 2500000, '2024-01-15 09:30:00'),
            ('Manchester Hospital Wing', 2, 1800000, '2024-01-16 14:20:00'),
            ('Birmingham Retail Complex', 3, 3200000, '2024-01-17 11:45:00'),
            ('Glasgow School Refurbishment', 4, 850000, '2024-01-18 10:15:00'),
            ('Leeds Office Tower', 5, 4100000, '2024-01-19 16:30:00'),
            ('Liverpool Waterfront Park', 5, 1200000, '2024-01-20 13:10:00'),
            ('Bristol Housing Development', 7, 2800000, '2024-01-21 08:45:00'),
            ('Edinburgh Museum Extension', 8, 1950000, '2024-01-22 15:25:00'),
            ('Cardiff Sports Centre', 9, 1650000, '2024-01-23 12:50:00'),
            ('Newcastle Industrial Estate', 10, 2200000, '2024-01-24 09:15:00'),
            ('Sheffield Tram Line Upgrade', 11, 2750000, '2024-01-25 14:40:00'),
            ('Nottingham Shopping Mall', 12, 3350000, '2024-01-26 11:05:00'),
            ('Southampton Port Facilities', 12, 1850000, '2024-01-27 16:20:00'),
            ('Portsmouth Naval Base Works', 12, 4200000, '2024-01-28 13:35:00'),
            ('Leicester University Campus', 15, 1550000, '2024-01-29 10:55:00'),
            ('Brighton Seafront Project', 16, 1350000, '2024-01-30 08:25:00'),
            ('Coventry Automotive Plant', 17, 2950000, '2024-01-31 15:45:00'),
            ('Hull Dock Regeneration', 18, 1750000, '2024-02-01 12:10:00'),
            ('Stoke Industrial Units', 19, 950000, '2024-02-02 09:35:00'),
            ('Derby Railway Station', 20, 2100000, '2024-02-03 14:55:00'),
            ('Reading Business Park', 21, 2450000, '2024-02-04 11:20:00'),
            ('Newport Distribution Centre', 22, 1650000, '2024-02-05 16:40:00'),
            ('Preston Civic Centre', 23, 1250000, '2024-02-06 13:05:00'),
            ('Swansea Marina Development', 24, 1850000, '2024-02-07 10:30:00'),
            ('Bradford Retail Park', 25, 1450000, '2024-02-08 08:50:00'),
            ('Sunderland Shipyard Works', 26, 1950000, '2024-02-09 15:15:00'),
            ('Luton Airport Expansion', 27, 3850000, '2024-02-10 12:35:00'),
            ('Wolverhampton College', 28, 1150000, '2024-02-11 09:55:00'),
            ('Plymouth Coastal Defence', 29, 2250000, '2024-02-12 14:15:00'),
            ('York Heritage Restoration', 30, 950000, '2024-02-13 11:40:00'),
            ('Bolton Town Hall Refurb', 31, 850000, '2024-02-14 16:05:00'),
            ('Peterborough Warehouse', 32, 1350000, '2024-02-15 13:25:00'),
            ('Stockport Bridge Works', 33, 750000, '2024-02-16 10:45:00'),
            ('Brighton Pier Maintenance', 34, 650000, '2024-02-17 08:10:00'),
            ('West Bromwich Factory', 35, 1850000, '2024-02-18 15:30:00'),
            ('Milton Keynes Data Centre', 36, 2750000, '2024-02-19 12:50:00');
    """

    count_tender_sql = "SELECT COUNT(*) FROM tender;"
    select_tender_sql = "SELECT * FROM tender LIMIT 20;"

    with psql_conn.cursor() as cur:
        cur.execute(insert_tender_sql)
        psql_conn.commit()

        cur.execute(count_tender_sql)
        count = cur.fetchone()[0]
        cur.execute(select_tender_sql)
        res = cur.fetchall()
        logger.info("%s of %s rows in tender table sent to output", len(res), count)
        return res


def seed_tender_line_item(
    psql_conn,
    num_tenders: int,
    num_services: int,
    num_job_titles: int,
    min_rows_per_tender: int,
    max_rows_per_tender: int,
):
    # Fetch valid labour_cost pairs from the database
    with psql_conn.cursor() as cur:
        cur.execute("SELECT service_id, title_engaged_id FROM labour_cost")
        valid_pairs = set((row[0], row[1]) for row in cur.fetchall())

    gen = TenderLineItemGenerator(
        num_tenders,
        num_services,
        num_job_titles,
        min_rows_per_tender,
        max_rows_per_tender,
        valid_pairs,
    )
    rows = gen.generate_rows()

    insert_sql = """
        INSERT INTO tenders_services_job_titles
            (tender_id, service_id, title_engaged_id, total_number_pa, hourly_price_override_gbp)
        VALUES (%s, %s, %s, %s, %s)
    """

    count_sql = "SELECT COUNT(*) FROM tenders_services_job_titles;"
    select_sql = "SELECT * FROM tenders_services_job_titles LIMIT 20;"

    with psql_conn.cursor() as cur:
        cur.executemany(insert_sql, rows)
        psql_conn.commit()

        cur.execute(count_sql)
        count = cur.fetchone()[0]
        cur.execute(select_sql)
        res = cur.fetchall()
        logger.info("%s rows in table, %s rows fetched", count, len(res))
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
        num_job_titles = 14
        num_services = 100
        num_consumables = 100

        logger.info("(Re-)initializing database")
        results["tables_in_db"] = initialize_database(conn)
        logger.info("Seeding department table")
        results["rows_in_department"] = seed_department(conn)
        logger.info("Seeding job_title table")
        results["rows_in_job_title"] = seed_job_title(conn)
        logger.info("Seeding consumable table")
        results["rows_from_consumable"] = seed_consumable(conn, num_consumables)
        logger.info("Seeding service table")
        results["rows_from_service"] = seed_service(conn, num_services)
        logger.info("Seeding overhead_cost table")
        results["rows_from_overhead_cost"] = seed_overhead_cost(conn, 100)
        logger.info("Seeding labour_cost table")
        results["rows_from_labour_cost"] = seed_labour_cost(
            conn, 100, num_services, num_job_titles
        )
        logger.info("Seeding direct_cost table")
        results["rows_from_direct_cost"] = seed_direct_cost(
            conn, 100, num_services, num_consumables
        )
        logger.info("Seeding client table")
        results["rows_in_client"] = seed_client(conn)
        logger.info("Seeding tender table")
        results["rows_in_tender"] = seed_tender(conn)
        logger.info("Seeding tenders_services_job_titles")
        results["rows_in_tenders_services_job_titles"] = seed_tender_line_item(
            conn, 36, num_services, num_job_titles, 5, 20
        )

    return {"statusCode": 200, "body": json.dumps(results, default=str)}
