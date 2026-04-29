import os
from decimal import Decimal
from datetime import datetime
import json
import logging
import psycopg_pool
from psycopg.sql import SQL, Identifier, Placeholder
from psycopg.rows import dict_row
from aws_lambda_powertools.event_handler import (
    APIGatewayHttpResolver,
    # Response,
)
from aws_lambda_powertools.utilities.typing.lambda_context import LambdaContext
import boto3
from botocore.exceptions import ClientError
# import psycopg
# from aws_lambda_powertools import Logger


logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (Decimal, datetime)):
            return str(o)
        return super().default(o)


def custom_serializer(o):
    return json.dumps(o, separators=(",", ":"), cls=CustomJSONEncoder)


app = APIGatewayHttpResolver(serializer=custom_serializer)


class DatabaseManager:
    def __init__(self):
        self._connection_pool = None
        self._connection = None
        self._secret_cache = None

    def _get_secrets(self):
        """Fetch secrets from Secrets Manager with caching"""
        if self._secret_cache is None:
            # Logic to fetch RDS connection details using SSM Secret
            # TO BE MODULARIZED
            secrets_manager = boto3.client("secretsmanager")
            logger.info("Fetching RDS login secret")
            try:
                rds_secret = secrets_manager.get_secret_value(
                    SecretId=os.environ["RDS_LOGIN_SECRET"]
                )
                rds_secret_json = json.loads(rds_secret["SecretString"])
            except ClientError as e:
                logger.error("Failed to fetch first secret: %s", e)
                raise
            logger.info("Fetching RDS master user secret")
            try:
                rds_user_secret = secrets_manager.get_secret_value(
                    SecretId=rds_secret_json["user_secret"]
                )
                rds_user_secret_json = json.loads(rds_user_secret["SecretString"])
                self._secret_cache = {
                    "host": rds_secret_json["host"],
                    "port": rds_secret_json["port"],
                    "dbname": rds_secret_json["dbname"],
                    "user": rds_user_secret_json["username"],
                    "password": rds_user_secret_json["password"],
                }
            except ClientError as e:
                logger.error("Failed to fetch second secret: %s", e)
                raise

        return self._secret_cache

    def _init_pool(self):
        """Initialize connection pool"""
        if self._connection_pool is None:
            config = self._get_secrets()

            conninfo = " ".join(f"{key}={value}" for key, value in config.items())
            self._connection_pool = psycopg_pool.ConnectionPool(
                conninfo=conninfo,
                min_size=1,
                max_size=20,
                open=True,  # Open the pool immediately
            )

            logger.info("Database connection initialized")

    def get_connection(self):
        """Get a connection from the pool"""
        self._init_pool()

        logger.info("Getting a connection from the pool")
        return self._connection_pool.connection()

    def close_all(self):
        """Close all connections in the pool"""
        if self._connection_pool:
            self._connection_pool.close()
            logger.info("All database connections closed")


# Global instance persists across warm starts
db_manager = DatabaseManager()


class DatabaseCursor:
    """Context manager for database operations"""

    def __init__(self, row_factory=None):
        self.conn_context = None
        self.connection = None
        self.cursor = None
        self.row_factory = row_factory or dict_row

    def __enter__(self):
        # Get connection from pool
        self.conn_context = db_manager.get_connection()
        self.connection = self.conn_context.__enter__()

        self.cursor = self.connection.cursor(row_factory=self.row_factory)
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            # Rollback on error
            self.connection.rollback()
        else:
            # Commit on success
            self.connection.commit()

        # Close cursor and return connection to pool
        self.cursor.close()
        self.conn_context.__exit__(exc_type, exc_val, exc_tb)
        return False  # Ensure exceptions propagate


@app.get("/department")
def get_department() -> None:
    """GET method for department table"""

    get_department_sql = """
        SELECT *
        FROM department
    """

    with DatabaseCursor() as cursor:
        cursor.execute(get_department_sql)
        results = cursor.fetchall()

    return results


@app.get("/job-title")
def get_job_title() -> list:
    """GET method for job_title table"""
    max_per_page = 100

    page = app.current_event.query_string_parameters.get("page", 1)
    page = max(int(page), 1)
    per_page = app.current_event.query_string_parameters.get("per_page", 10)
    per_page = min(max(int(per_page), 1), max_per_page)

    offset = per_page * (page - 1)

    get_sql = SQL("""
        SELECT
            jt.id
            ,d.name AS department
            ,jt.title
            ,jt.default_ft_weekly_hours
            ,jt.default_lunch_break_hours
            ,jt.hourly_rate_gbp
            ,jt.default_annual_holiday_days
            ,jt.default_annual_training_days
            ,jt.default_annual_sick_days
        FROM job_title jt
        LEFT OUTER JOIN department d
            ON jt.department_id = d.id
        ORDER BY jt.id
        LIMIT {per_page}
        OFFSET {offset}
    """).format(per_page=per_page, offset=offset)

    with DatabaseCursor() as cursor:
        cursor.execute(get_sql)
        results = cursor.fetchall()

    return results

    # access query strings as app.current_event.query_string_parameters (dict)
    # access headers as app.current_event.headers (case-insentive dict)
    # access path (?) as app.current_event.path
    # see https://docs.aws.amazon.com/powertools/python/latest/core/event_handler/api_gateway/#raising-http-errors


@app.get("/job-title/titles")
def get_job_title_titles() -> list:
    """Method to GET all titles in the job_title table"""

    get_titles_sql = """
        SELECT
            id
            ,title
        FROM job_title
        ORDER BY title
    """

    with DatabaseCursor() as cursor:
        cursor.execute(get_titles_sql)
        results = cursor.fetchall()

    return results


@app.post("/job-title")
def post_job_title() -> None:
    """POST method for job_title table"""

    columns = (
        "department",
        "title",
        "default_ft_weekly_hours",
        "default_lunch_break_hours",
        "hourly_rate_gbp",
        "default_annual_holiday_days",
        "default_annual_training_days",
        "default_annual_sick_days",
    )

    rows = json.loads(app.current_event.body)
    if isinstance(rows, dict):
        # Ensure rows is a list of dicts to support multi-row insert
        rows = [rows]

    values = [row[column] for column in columns for row in rows]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO job_title ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        cursor.execute(post_sql, values)


@app.patch("/job-title/<job_title_id>")
def patch_job_title(job_title_id: str) -> None:
    """PATCH method for job_title table"""

    logger.info("PATCHing job title ID: %s", job_title_id)
    logger.info(app.current_event.body)

    updated_columns = json.loads(app.current_event.body)

    set_parts = []
    values = []
    for col, val in updated_columns.items():
        set_parts.append(SQL("{} = %s").format(Identifier(col)))
        values.append(val)

    patch_sql = SQL("UPDATE job_title SET {} WHERE ID = %s").format(
        SQL(", ").join(set_parts)
    )

    with DatabaseCursor() as cursor:
        cursor.execute(patch_sql, values + [int(job_title_id)])


@app.get("/consumable")
def get_consumable() -> list:
    """GET method for consumable table"""
    max_per_page = 100

    page = app.current_event.query_string_parameters.get("page", 1)
    page = max(int(page), 1)
    per_page = app.current_event.query_string_parameters.get("per_page", 10)
    per_page = min(max(int(per_page), 1), max_per_page)

    offset = per_page * (page - 1)

    get_sql = SQL("""
        SELECT *
        FROM consumable
        LIMIT {per_page}
        OFFSET {offset}
    """).format(per_page=per_page, offset=offset)

    with DatabaseCursor() as cursor:
        cursor.execute(get_sql)
        results = cursor.fetchall()

    return results


@app.get("/consumable/names")
def get_consumable_names() -> list:
    """Method to GET all consumable names in the consumable table"""

    get_consumable_names_sql = """
        SELECT
            id
            ,consumable_name
        FROM consumable
        ORDER BY
            consumable_name
    """

    with DatabaseCursor() as cursor:
        cursor.execute(get_consumable_names_sql)
        results = cursor.fetchall()

    return results


@app.post("/consumable")
def post_consumable() -> None:
    """POST method for consumable table"""

    columns = ("consumable_name", "default_unit_cost_gbp")

    rows = json.loads(app.current_event.body)
    if isinstance(rows, dict):
        # Ensure rows is a list of dicts to support multi-row insert
        rows = [rows]

    logger.info("POST into consumable values:")
    logger.info(rows)

    values = [row[column] for column in columns for row in rows]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO consumable ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


@app.patch("/consumable/<consumable_id>")
def patch_consumable(consumable_id: str) -> None:
    """PATCH method for consumable table"""

    logger.info("PATCHing consumable ID: %s", consumable_id)
    logger.info(app.current_event.body)

    updated_columns = json.loads(app.current_event.body)

    set_parts = []
    values = []
    for col, val in updated_columns.items():
        set_parts.append(SQL("{} = %s").format(Identifier(col)))
        values.append(val)

    patch_sql = SQL("UPDATE consumable SET {} WHERE ID = %s").format(
        SQL(", ").join(set_parts)
    )

    with DatabaseCursor() as cursor:
        cursor.execute(patch_sql, values + [int(consumable_id)])


@app.get("/service")
def get_service() -> list:
    """GET method for service table"""
    max_per_page = 100

    page = app.current_event.query_string_parameters.get("page", 1)
    page = max(int(page), 1)
    per_page = app.current_event.query_string_parameters.get("per_page", 10)
    per_page = min(max(int(per_page), 1), max_per_page)

    offset = per_page * (page - 1)

    get_sql = SQL("""
        SELECT *
        FROM service
        LIMIT {per_page}
        OFFSET {offset}
    """).format(per_page=per_page, offset=offset)

    with DatabaseCursor() as cursor:
        cursor.execute(get_sql)
        results = cursor.fetchall()

    logger.info(results)
    return results


@app.get("/service/slugs")
def get_service_slugs() -> list:
    """Method to GET all service slugs in the service table"""

    get_service_slugs_sql = """
        SELECT
            id AS service_id
            ,category || ': ' || service_name AS service_slug
        FROM service
        ORDER BY service_slug
    """

    with DatabaseCursor() as cursor:
        cursor.execute(get_service_slugs_sql)
        results = cursor.fetchall()

    return results


@app.post("/service")
def post_service() -> None:
    """POST method for service table"""

    columns = (
        "pillar",
        "category",
        "service_name",
        "xero_code",
        "overhead_recovery_on_labour_percentage",
        "required_profit_margin_percentage",
        "acceptable_market_price_gbp",
        "our_current_hourly_price_gbp",
        "new_hourly_price_gbp",
        "new_day_rate_gbp",
        "comments",
    )

    rows = json.loads(app.current_event.body)
    if isinstance(rows, dict):
        # Ensure rows is a list of dicts to support multi-row insert
        rows = [rows]

    logger.info("POST into service values:")
    logger.info(rows)

    values = [
        row[column] if row[column] != "null" else None
        for column in columns
        for row in rows
    ]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO service ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


@app.patch("/service/<service_id>")
def patch_service(service_id: str) -> None:
    """PATCH method for service table"""

    logger.info("PATCHing service ID: %s", service_id)
    logger.info(app.current_event.body)

    updated_columns = json.loads(app.current_event.body)

    set_parts = []
    values = []
    for col, val in updated_columns.items():
        set_parts.append(SQL("{} = %s").format(Identifier(col)))
        values.append(val)

    patch_sql = SQL("UPDATE service SET {} WHERE ID = %s").format(
        SQL(", ").join(set_parts)
    )

    with DatabaseCursor() as cursor:
        cursor.execute(patch_sql, values + [int(service_id)])


@app.get("/overhead-cost")
def get_overhead_cost() -> list:
    """GET method for overhead_cost table"""
    max_per_page = 100

    page = app.current_event.query_string_parameters.get("page", 1)
    page = max(int(page), 1)
    per_page = app.current_event.query_string_parameters.get("per_page", 10)
    per_page = min(max(int(per_page), 1), max_per_page)

    offset = per_page * (page - 1)

    get_overhead_cost_sql = SQL("""
        SELECT *
        FROM overhead_cost
        LIMIT {per_page}
        OFFSET {offset}
    """).format(per_page=per_page, offset=offset)

    with DatabaseCursor() as cursor:
        cursor.execute(get_overhead_cost_sql)
        results = cursor.fetchall()

    logger.info(results)
    return results


@app.post("/overhead-cost")
def post_overhead_cost() -> None:
    """POST method for overhead_cost table"""

    columns = ("cost_type", "cost_description", "budgeted_spend_gbp")

    rows = json.loads(app.current_event.body)
    if isinstance(rows, dict):
        # Ensure rows is a list of dicts to support multi-row insert
        rows = [rows]

    logger.info("POST into overhead_cost values:")
    logger.info(rows)

    values = [
        row[column] if row[column] != "null" else None
        for column in columns
        for row in rows
    ]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_overhead_cost_sql = SQL("INSERT INTO overhead_cost ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        # logger.info(post_overhead_cost_sql.as_string(cursor))
        cursor.execute(post_overhead_cost_sql, values)


@app.patch("/overhead-cost/<overhead_cost_id>")
def patch_overhead_cost(overhead_cost_id: str) -> None:
    """PATCH method for overhead_cost table"""

    logger.info("PATCHing overhead_cost ID: %s", overhead_cost_id)
    logger.info(app.current_event.body)

    updated_columns = json.loads(app.current_event.body)

    set_parts = []
    values = []
    for col, val in updated_columns.items():
        set_parts.append(SQL("{} = %s").format(Identifier(col)))
        values.append(val)

    patch_overhead_cost_sql = SQL("UPDATE overhead_cost SET {} WHERE ID = %s").format(
        SQL(", ").join(set_parts)
    )

    with DatabaseCursor() as cursor:
        cursor.execute(patch_overhead_cost_sql, values + [int(overhead_cost_id)])


@app.get("/labour-cost")
def get_labour_cost() -> list:
    """GET method for labour_cost table"""
    max_per_page = 100

    page = app.current_event.query_string_parameters.get("page", 1)
    page = max(int(page), 1)
    per_page = app.current_event.query_string_parameters.get("per_page", 10)
    per_page = min(max(int(per_page), 1), max_per_page)

    offset = per_page * (page - 1)

    get_labour_cost_sql = SQL("""
        SELECT
            lc.service_id
            ,s.service_name AS service
            ,lc.title_engaged_id
            ,jt.title AS title_engaged
            ,lc.required_time_mins
        FROM labour_cost lc
        LEFT OUTER JOIN service s
            ON lc.service_id = s.id
        LEFT OUTER JOIN job_title jt
            ON lc.title_engaged_id = jt.id
        ORDER BY
            service
            ,title_engaged
        LIMIT {per_page}
        OFFSET {offset}
    """).format(per_page=per_page, offset=offset)
    with DatabaseCursor() as cursor:
        cursor.execute(get_labour_cost_sql)
        results = cursor.fetchall()

    logger.info(results)
    return results


@app.post("/labour-cost")
def post_labour_cost() -> None:
    """POST method for labour_cost table"""

    columns = ("service_id", "title_engaged_id", "required_time_mins")

    rows = json.loads(app.current_event.body)
    if isinstance(rows, dict):
        # Ensure rows is a list of dicts to support multi-row insert
        rows = [rows]

    logger.info("POST into labour_cost values:")
    logger.info(rows)

    values = [
        row[column] if row[column] != "null" else None
        for column in columns
        for row in rows
    ]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO labour_cost ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


@app.patch("/labour-cost/<service_id>/<title_engaged_id>")
def patch_labour_cost(service_id: str, title_engaged_id: str) -> None:
    """PATCH method for labour_cost table"""

    logger.info(
        "PATCHing labour_cost with service ID %s and job title ID %s",
        service_id,
        title_engaged_id,
    )
    logger.info(app.current_event.body)

    updated_required_time = json.loads(app.current_event.body).get(
        "required_time_mins", None
    )
    if not updated_required_time:
        return None

    patch_labour_cost_sql = """
            UPDATE labour_cost
            SET required_time_mins = %s
            WHERE service_id = %s
                AND title_engaged_id = %s 
            """

    with DatabaseCursor() as cursor:
        cursor.execute(
            patch_labour_cost_sql,
            [updated_required_time, int(service_id), int(title_engaged_id)],
        )


@app.get("/direct-cost")
def get_direct_cost() -> list:
    """GET method for direct_cost table"""
    max_per_page = 100

    page = app.current_event.query_string_parameters.get("page", 1)
    page = max(int(page), 1)
    per_page = app.current_event.query_string_parameters.get("per_page", 10)
    per_page = min(max(int(per_page), 1), max_per_page)

    offset = per_page * (page - 1)

    get_direct_cost_sql = SQL("""
        SELECT
            dc.service_id
            ,s.service_name AS service
            ,dc.consumable_id
            ,c.consumable_name AS consumable
            ,dc.cost_gbp
        FROM direct_cost dc
        LEFT OUTER JOIN service s
            ON dc.service_id = s.id
        LEFT OUTER JOIN consumable c
            ON dc.consumable_id = c.id
        ORDER BY
            service
            ,consumable
        LIMIT {per_page}
        OFFSET {offset}
    """).format(per_page=per_page, offset=offset)
    with DatabaseCursor() as cursor:
        cursor.execute(get_direct_cost_sql)
        results = cursor.fetchall()

    logger.info(results)
    return results


@app.post("/direct-cost")
def post_direct_cost() -> None:
    """POST method for direct_cost table"""

    columns = ("service_id", "consumable_id", "cost_gbp")

    rows = json.loads(app.current_event.body)
    if isinstance(rows, dict):
        # Ensure rows is a list of dicts to support multi-row insert
        rows = [rows]

    logger.info("POST into direct_cost values:")
    logger.info(rows)

    values = [
        row[column] if row[column] != "null" else None
        for column in columns
        for row in rows
    ]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO direct_cost ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


@app.patch("/direct-cost/<service_id>/<consumable_id>")
def patch_direct_cost(service_id: str, consumable_id: str) -> None:
    """PATCH method for direct_cost table"""

    logger.info(
        "PATCHing direct_cost with service ID %s and consumable ID %s",
        service_id,
        consumable_id,
    )
    logger.info(app.current_event.body)

    updated_cost = json.loads(app.current_event.body).get("cost_gbp", None)
    if not updated_cost:
        return None

    patch_direct_cost_sql = """
            UPDATE direct_cost
            SET cost_gbp = %s
            WHERE service_id = %s
                AND consumable_id = %s
            """

    with DatabaseCursor() as cursor:
        cursor.execute(
            patch_direct_cost_sql,
            [updated_cost, int(service_id), int(consumable_id)],
        )


@app.get("/client")
def get_client() -> list:
    """GET method for client table"""
    max_per_page = 100

    page = app.current_event.query_string_parameters.get("page", 1)
    page = max(int(page), 1)
    per_page = app.current_event.query_string_parameters.get("per_page", 10)
    per_page = min(max(int(per_page), 1), max_per_page)

    offset = per_page * (page - 1)

    get_sql = SQL("""
        SELECT * FROM client
        ORDER BY client_name
        LIMIT {per_page}
        OFFSET {offset}
    """).format(per_page=per_page, offset=offset)

    with DatabaseCursor() as cursor:
        cursor.execute(get_sql)
        results = cursor.fetchall()

    return results


@app.post("/client")
def post_client() -> None:
    """POST method for client table"""

    columns = ("client_name",)

    rows = json.loads(app.current_event.body)
    if isinstance(rows, dict):
        # Ensure rows is a list of dicts to support multi-row insert
        rows = [rows]

    logger.info("POST into client values:")
    logger.info(rows)

    values = [row[column] for column in columns for row in rows]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO client ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


@app.patch("/client/<client_id>")
def patch_client(client_id: str) -> None:
    """PATCH method for client table"""

    logger.info("PATCHing client ID: %s", client_id)
    logger.info(app.current_event.body)

    updated_client_name = json.loads(app.current_event.body).get("client_name", None)
    if not updated_client_name:
        return None

    patch_direct_cost_sql = """
            UPDATE client
            SET client_name = %s
            WHERE id = %s
            """

    with DatabaseCursor() as cursor:
        cursor.execute(
            patch_direct_cost_sql,
            [updated_client_name, int(client_id)],
        )

    return None


@app.get("/tender")
def get_tender() -> list:
    """GET method for tender table"""
    max_per_page = 100

    page = app.current_event.query_string_parameters.get("page", 1)
    page = max(int(page), 1)
    per_page = app.current_event.query_string_parameters.get("per_page", 10)
    per_page = min(max(int(per_page), 1), max_per_page)

    offset = per_page * (page - 1)

    get_sql = SQL("""
        SELECT
            t.id
            ,t.tender_title
            ,t.client_id
            ,c.client_name as client
            ,t.projected_sales_value_gbp
            ,t.date_created
        FROM tender t
        LEFT OUTER JOIN client c
            ON t.client_id = c.id
        ORDER BY t.id
        LIMIT {per_page}
        OFFSET {offset}
    """).format(per_page=per_page, offset=offset)

    with DatabaseCursor() as cursor:
        cursor.execute(get_sql)
        results = cursor.fetchall()

    return results


@app.post("/tender")
def post_tender() -> None:
    """POST method for tender table"""

    columns = ("tender_title", "client_id", "projected_sales_value_gbp", "date_created")

    rows = json.loads(app.current_event.body)
    if isinstance(rows, dict):
        # Ensure rows is a list of dicts to support multi-row insert
        rows = [rows]

    logger.info("POST into tender values:")
    logger.info(rows)

    values = [row[column] for column in columns for row in rows]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO tender ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


@app.patch("/tender/<tender_id>")
def patch_tender(tender_id: str) -> None:
    """PATCH method for tender table"""

    logger.info("PATCHing tender ID: %s", tender_id)
    logger.info(app.current_event.body)

    updated_columns = json.loads(app.current_event.body)

    set_parts = []
    values = []
    for col, val in updated_columns.items():
        set_parts.append(SQL("{} = %s").format(Identifier(col)))
        values.append(val)

    patch_sql = SQL("UPDATE tender SET {} WHERE ID = %s").format(
        SQL(", ").join(set_parts)
    )

    with DatabaseCursor() as cursor:
        cursor.execute(patch_sql, values + [int(tender_id)])


@app.get("/tender/line-items/<tender_id>")
def get_tender_line_items(tender_id: str) -> list:
    """GET method for tenders_services_job_titles table"""
    max_per_page = 100

    page = app.current_event.query_string_parameters.get("page", 1)
    page = max(int(page), 1)
    per_page = app.current_event.query_string_parameters.get("per_page", 10)
    per_page = min(max(int(per_page), 1), max_per_page)

    offset = per_page * (page - 1)

    get_sql = SQL("""
        WITH filtered_tender_line_items AS (
            SELECT *
            FROM tenders_services_job_titles
            WHERE tender_id = {tender_id}
        )
        SELECT
            ft.tender_id
            ,t.tender_title
            ,ft.service_id
            ,s.service_name AS service
            ,ft.title_engaged_id
            ,jt.title AS title_engaged
            ,ft.quantity_pa
            ,lc.required_time_mins AS duration_mins
            ,ft.hourly_price_override_gbp
        FROM filtered_tender_line_items ft
        LEFT OUTER JOIN tender t
            ON ft.tender_id = t.id
        LEFT OUTER JOIN service s
            ON ft.service_id = s.id
        LEFT OUTER JOIN job_title jt
            ON ft.title_engaged_id = jt.id
        LEFT OUTER JOIN labour_cost lc
            ON (
                ft.service_id = lc.service_id
                AND ft.title_engaged_id = lc.title_engaged_id
            )
        ORDER BY
            ft.tender_id
            ,ft.service_id
            ,ft.title_engaged_id
        LIMIT {per_page}
        OFFSET {offset}
    """).format(tender_id=tender_id, per_page=per_page, offset=offset)

    with DatabaseCursor() as cursor:
        cursor.execute(get_sql)
        results = cursor.fetchall()

    return results


@app.post("/tender/line-items")
def post_tender_line_items() -> None:
    """POST method for tenders_services_job_titles table"""

    columns = (
        "tender_id",
        "service_id",
        "title_engaged_id",
        "quantity_pa",
        # "duration_minutes",
        "hourly_price_override_gbp",
    )

    rows = json.loads(app.current_event.body)
    if isinstance(rows, dict):
        # Ensure rows is a list of dicts to support multi-row insert
        rows = [rows]

    logger.info("POST into tenders_services_job_titles values:")
    logger.info(rows)

    values = [row[column] for column in columns for row in rows]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO tenders_services_job_titles ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


@app.patch("/tender/line-items/<tender_id>/<service_id>/<title_engaged_id>")
def patch_tender_line_item(
    tender_id: str, service_id: str, title_engaged_id: str
) -> None:
    """PATCH method for tenders_services_job_titles table"""

    logger.info(
        "PATCHing tenders_services_job_titles ID %s, service ID %s, job title ID %s",
        tender_id,
        service_id,
        title_engaged_id,
    )
    logger.info(app.current_event.body)

    updated_columns = json.loads(app.current_event.body)

    set_parts = []
    values = []
    for col, val in updated_columns.items():
        set_parts.append(SQL("{} = %s").format(Identifier(col)))
        values.append(val)

    patch_sql = SQL("""
        UPDATE tenders_services_job_titles
        SET {}
        WHERE tender_id = %s
          AND service_id = %s
          AND title_engaged_id = %s
    """).format(
        SQL(", ").join(set_parts)
    )

    with DatabaseCursor() as cursor:
        cursor.execute(patch_sql, values + [tender_id, service_id, title_engaged_id])


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    response = app.resolve(event, context)

    # If Lambda is about to be destroyed, clean up
    if context.get_remaining_time_in_millis() < 100:
        db_manager.close_all()

    return response
