import os
from decimal import Decimal
from datetime import datetime
import json
import logging

from typing import Optional, TypeVar, ClassVar, Type, TypeAlias
from typing_extensions import Annotated
from pydantic import RootModel, BaseModel, Field, BeforeValidator, model_validator
from pydantic_strict_partial import create_partial_model

import psycopg_pool
from psycopg.sql import SQL, Identifier, Placeholder
from psycopg.rows import dict_row

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.openapi.params import Query, Body
from aws_lambda_powertools.utilities.typing.lambda_context import LambdaContext
import boto3
from botocore.exceptions import ClientError
# from aws_lambda_powertools import Logger


logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)


def empty_to_none(value: str | Decimal | None) -> Decimal | None:
    """
    Convert empty strings to None for optional Decimal fields.

    This validator runs before Pydantic's built-in validation,
    so empty strings are treated as None instead of raising an error.
    """
    if value == "":
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(value)


def OptionalDecimal(max_digits: int, decimal_places: int) -> TypeAlias:
    """
    Create an Optional Decimal type with empty string handling and constraints.

    Args:
        max_digits: Maximum total number of digits
        decimal_places: Maximum number of decimal places

    Returns:
        A type alias that can be used in Pydantic models
    """
    return Annotated[
        None
        | Annotated[
            Decimal, Field(max_digits=max_digits, decimal_places=decimal_places)
        ],
        BeforeValidator(empty_to_none),
    ]


class Pagination(BaseModel):
    page: Optional[int] = 1
    per_page: Optional[int] = 10


# class Department(BaseModel):
#     id: int
#     name: Annotated[str, Field(max_length=50)]


class JobTitle(BaseModel):
    department_id: int
    title: Annotated[str, Field(max_length=50)]
    default_ft_weekly_hours: Annotated[Decimal, Field(max_digits=3, decimal_places=1)]
    default_lunch_break_hours: Annotated[Decimal, Field(max_digits=2, decimal_places=1)]
    hourly_rate_gbp: Annotated[Decimal, Field(max_digits=7, decimal_places=2)]
    default_annual_holiday_days: OptionalDecimal(3, 1) = None
    default_annual_training_days: OptionalDecimal(3, 1) = None
    default_annual_sick_days: OptionalDecimal(3, 1) = None


UpdateJobTitle = create_partial_model(JobTitle)


class Consumable(BaseModel):
    consumable_name: Annotated[str, Field(max_length=100)]
    default_unit_cost_gbp: Optional[
        Annotated[Decimal, Field(max_digits=6, decimal_places=2)]
    ] = None


UpdateConsumable = create_partial_model(Consumable)


class Service(BaseModel):
    pillar: Annotated[str, Field(max_length=50)]
    category: Annotated[str, Field(max_length=50)]
    service_name: Annotated[str, Field(max_length=75)]
    xero_code: Annotated[int, Field(ge=0, le=9999)]
    overhead_recovery_on_labour_percentage: int
    required_profit_margin_percentage: Annotated[
        Decimal, Field(max_digits=4, decimal_places=2)
    ]
    acceptable_market_price_gbp: Annotated[
        Decimal, Field(max_digits=8, decimal_places=2)
    ]
    our_current_unit_price_gbp: Annotated[
        Decimal, Field(max_digits=8, decimal_places=2)
    ]
    new_unit_price_gbp: Optional[
        Annotated[Decimal, Field(max_digits=8, decimal_places=2)]
    ] = None
    new_day_rate_gbp: Optional[
        Annotated[Decimal, Field(max_digits=9, decimal_places=2)]
    ] = None
    comments: Optional[Annotated[str, Field(max_length=100)]] = None


UpdateService = create_partial_model(Service)


class OverheadCost(BaseModel):
    cost_type: Annotated[str, Field(max_length=30)]
    cost_description: Annotated[str, Field(max_length=30)]
    budgeted_spend_gbp: int


UpdateOverheadCost = create_partial_model(OverheadCost)


class LabourCost(BaseModel):
    service_id: int
    title_engaged_id: int
    required_time_mins: int


UpdateLabourCost = create_partial_model(LabourCost)


class DirectCost(BaseModel):
    service_id: int
    consumable_id: int
    cost_gbp: Annotated[Decimal, Field(max_digits=5, decimal_places=2)]


UpdateDirectCost = create_partial_model(DirectCost)


class Client(BaseModel):
    client_name: Annotated[str, Field(max_length=50)]


UpdateClient = create_partial_model(Client)


class Tender(BaseModel):
    tender_title: Annotated[str, Field(max_length=50)]
    client_id: int
    projected_sales_value_gbp: int
    date_created: datetime


UpdateTender = create_partial_model(Tender)


class TenderLineItem(BaseModel):
    tender_id: int
    service_id: int
    total_number_pa: int
    unit_price_override_gbp: Optional[
        Annotated[Decimal, Field(max_digits=8, decimal_places=2)]
    ] = None


UpdateTenderLineItem = create_partial_model(TenderLineItem)


T = TypeVar("T", bound="BaseModel")


def create_lax_list_model(model: Type[T]) -> Type[RootModel[list[T]]]:
    """
    Factory function: creates a RootModel that coerces a single dict
    into a list of dicts for *model*.
    """

    class LaxList(RootModel[list[model]]):
        item_model: ClassVar[type] = model

        @model_validator(mode="before")
        @classmethod
        def coerce_single(cls, values):
            return [values] if isinstance(values, dict) else values

        @model_validator(mode="after")
        def check_not_empty(self):
            if len(self.root) == 0:
                raise ValueError("at least one row object required")
            return self

    LaxList.__name__ = f"{model.__name__}List"
    LaxList.__module__ = model.__module__
    return LaxList


models_for_lax_list = [
    JobTitle,
    Consumable,
    Service,
    OverheadCost,
    LabourCost,
    DirectCost,
    Client,
    Tender,
    TenderLineItem,
]
lax_lists = {model: create_lax_list_model(model) for model in models_for_lax_list}


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (Decimal, datetime)):
            return str(o)
        return super().default(o)


def custom_serializer(o):
    return json.dumps(o, separators=(",", ":"), cls=CustomJSONEncoder)


app = APIGatewayHttpResolver(
    enable_validation=True,
    serializer=custom_serializer,
)


class DatabaseManager:
    def __init__(self):
        self._connection_pool = None
        self._connection = None
        self._secret_cache = None

    def _get_secrets(self):
        """Fetch secrets from Secrets Manager with caching"""
        if self._secret_cache is None:
            # Logic to fetch RDS connection details using SSM Secretn
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
def get_job_title(pagination: Annotated[Pagination, Query()]) -> list:
    """GET method for job_title table"""
    max_per_page = 100
    page = max(int(pagination.page), 1)
    per_page = min(max(int(pagination.per_page), 1), max_per_page)
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
def post_job_title(body: Annotated[lax_lists[JobTitle], Body()]) -> None:
    """POST method for job_title table"""

    columns = (
        "department_id",
        "title",
        "default_ft_weekly_hours",
        "default_lunch_break_hours",
        "hourly_rate_gbp",
        "default_annual_holiday_days",
        "default_annual_training_days",
        "default_annual_sick_days",
    )

    rows = body.root

    values = [row.model_dump()[column] for column in columns for row in rows]
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
def patch_job_title(job_title_id: str, body: Annotated[UpdateJobTitle, Body()]) -> None:
    """PATCH method for job_title table"""

    logger.info("PATCHing job title ID: %s", job_title_id)
    logger.info(app.current_event.body)

    updated_columns = body.model_dump(exclude_unset=True)

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
def get_consumable(pagination: Annotated[Pagination, Query()]) -> list:
    """GET method for consumable table"""
    max_per_page = 100
    page = max(int(pagination.page), 1)
    per_page = min(max(int(pagination.per_page), 1), max_per_page)
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
    """
    Method to GET all consumable names in the consumable table
    Used for populating consumable-selection dropdown lists
    """

    get_consumable_names_sql = """
        SELECT
            id AS consumable_id
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
def post_consumable(body: Annotated[lax_lists[Consumable], Body()]) -> None:
    """POST method for consumable table"""

    columns = ("consumable_name", "default_unit_cost_gbp")

    rows = body.root

    logger.info("POST into consumable values:")
    logger.info(rows)

    values = [row.model_dump()[column] for column in columns for row in rows]
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
def patch_consumable(
    consumable_id: str, body: Annotated[UpdateConsumable, Body()]
) -> None:
    """PATCH method for consumable table"""

    logger.info("PATCHing consumable ID: %s", consumable_id)
    logger.info(app.current_event.body)

    updated_columns = body.model_dump(exclude_unset=True)

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
def get_service(pagination: Annotated[Pagination, Query()]) -> list:
    """GET method for service table"""
    max_per_page = 100
    page = max(int(pagination.page), 1)
    per_page = min(max(int(pagination.per_page), 1), max_per_page)
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
def post_service(body: Annotated[lax_lists[Service], Body()]) -> None:
    """POST method for service table"""

    columns = (
        "pillar",
        "category",
        "service_name",
        "xero_code",
        "overhead_recovery_on_labour_percentage",
        "required_profit_margin_percentage",
        "acceptable_market_price_gbp",
        "our_current_unit_price_gbp",
        "new_unit_price_gbp",
        "new_day_rate_gbp",
        "comments",
    )

    rows = body.root

    logger.info("POST into service values:")
    logger.info(rows)

    values = [
        row.model_dump()[column] if row.model_dump()[column] != "null" else None
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
def patch_service(service_id: str, body: Annotated[UpdateService, Body()]) -> None:
    """PATCH method for service table"""

    logger.info("PATCHing service ID: %s", service_id)
    logger.info(app.current_event.body)

    updated_columns = body.model_dump(exclude_unset=True)

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
def get_overhead_cost(pagination: Annotated[Pagination, Query()]) -> list:
    """GET method for overhead_cost table"""
    max_per_page = 100
    page = max(int(pagination.page), 1)
    per_page = min(max(int(pagination.per_page), 1), max_per_page)
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
def post_overhead_cost(body: Annotated[lax_lists[OverheadCost], Body()]) -> None:
    """POST method for overhead_cost table"""

    columns = ("cost_type", "cost_description", "budgeted_spend_gbp")

    rows = body.root

    logger.info("POST into overhead_cost values:")
    logger.info(rows)

    values = [
        row.model_dump()[column] if row.model_dump()[column] != "null" else None
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
def patch_overhead_cost(
    overhead_cost_id: str, body: Annotated[UpdateOverheadCost, Body()]
) -> None:
    """PATCH method for overhead_cost table"""

    logger.info("PATCHing overhead_cost ID: %s", overhead_cost_id)
    logger.info(app.current_event.body)

    updated_columns = body.model_dump(exclude_unset=True)

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
def get_labour_cost(pagination: Annotated[Pagination, Query()]) -> list:
    """GET method for labour_cost table"""
    max_per_page = 100
    page = max(int(pagination.page), 1)
    per_page = min(max(int(pagination.per_page), 1), max_per_page)
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
def post_labour_cost(body: Annotated[lax_lists[LabourCost], Body()]) -> None:
    """POST method for labour_cost table"""

    columns = ("service_id", "title_engaged_id", "required_time_mins")

    rows = body.root

    logger.info("POST into labour_cost values:")
    logger.info(rows)

    values = [
        row.model_dump()[column] if row.model_dump()[column] != "null" else None
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
def patch_labour_cost(
    service_id: str, title_engaged_id: str, body: Annotated[UpdateLabourCost, Body()]
) -> None:
    """PATCH method for labour_cost table"""

    logger.info(
        "PATCHing labour_cost with service ID %s and job title ID %s",
        service_id,
        title_engaged_id,
    )
    logger.info(app.current_event.body)

    if "required_time_mins" not in body.model_fields_set:
        return None
    updated_required_time = body.model_dump()["required_time_mins"]

    patch_labour_cost_sql = SQL("""
            UPDATE labour_cost
            SET required_time_mins = %s
            WHERE service_id = %s
                AND title_engaged_id = %s 
    """)

    with DatabaseCursor() as cursor:
        cursor.execute(
            patch_labour_cost_sql,
            [updated_required_time, int(service_id), int(title_engaged_id)],
        )


@app.get("/direct-cost")
def get_direct_cost(pagination: Annotated[Pagination, Query()]) -> list:
    """GET method for direct_cost table"""
    max_per_page = 100
    page = max(int(pagination.page), 1)
    per_page = min(max(int(pagination.per_page), 1), max_per_page)
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
def post_direct_cost(body: Annotated[lax_lists[DirectCost], Body()]) -> None:
    """POST method for direct_cost table"""

    columns = ("service_id", "consumable_id", "cost_gbp")

    rows = body.root

    logger.info("POST into direct_cost values:")
    logger.info(rows)

    values = [
        row.model_dump()[column] if row.model_dump()[column] != "null" else None
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
def patch_direct_cost(
    service_id: str, consumable_id: str, body: Annotated[UpdateDirectCost, Body()]
) -> None:
    """PATCH method for direct_cost table"""

    logger.info(
        "PATCHing direct_cost with service ID %s and consumable ID %s",
        service_id,
        consumable_id,
    )
    logger.info(app.current_event.body)

    if "cost_gbp" not in body.model_fields_set:
        return None
    updated_cost = body.model_dump()["cost_gbp"]

    patch_direct_cost_sql = SQL("""
            UPDATE direct_cost
            SET cost_gbp = %s
            WHERE service_id = %s
                AND consumable_id = %s
    """)

    with DatabaseCursor() as cursor:
        cursor.execute(
            patch_direct_cost_sql,
            [updated_cost, int(service_id), int(consumable_id)],
        )


@app.get("/client")
def get_client(pagination: Annotated[Pagination, Query()]) -> list:
    """GET method for client table"""
    max_per_page = 100
    page = max(int(pagination.page), 1)
    per_page = min(max(int(pagination.per_page), 1), max_per_page)
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


@app.get("/client/names")
def get_client_names() -> list:
    """
    Method to GET all client names in the client table
    Used for populating client-selection dropdown lists
    """
    get_sql = SQL("""
        SELECT
            id AS client_id
            ,client_name
        FROM client
        ORDER BY client_name
    """)

    with DatabaseCursor() as cursor:
        cursor.execute(get_sql)
        results = cursor.fetchall()

    return results


@app.post("/client")
def post_client(body: Annotated[lax_lists[Client], Body()]) -> None:
    """POST method for client table"""

    columns = ("client_name",)

    rows = body.root

    logger.info("POST into client values:")
    logger.info(rows)

    values = [row.model_dump()[column] for column in columns for row in rows]
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
def patch_client(client_id: str, body: Annotated[UpdateClient, Body()]) -> None:
    """PATCH method for client table"""

    logger.info("PATCHing client ID: %s", client_id)
    logger.info(app.current_event.body)

    if "client_name" not in body.model_fields_set:
        return None
    updated_client_name = body.model_dump()["client_name"]

    patch_direct_cost_sql = SQL("""
            UPDATE client
            SET client_name = %s
            WHERE id = %s
    """)

    with DatabaseCursor() as cursor:
        cursor.execute(
            patch_direct_cost_sql,
            [updated_client_name, int(client_id)],
        )

    return None


@app.get("/tender")
def get_tender(pagination: Annotated[Pagination, Query()]) -> list:
    """GET method for tender table"""
    max_per_page = 100
    page = max(int(pagination.page), 1)
    per_page = min(max(int(pagination.per_page), 1), max_per_page)
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
        ORDER BY t.date_created DESC
        LIMIT {per_page}
        OFFSET {offset}
    """).format(per_page=per_page, offset=offset)

    with DatabaseCursor() as cursor:
        cursor.execute(get_sql)
        results = cursor.fetchall()

    return results


@app.get("/tender/single/<tender_id>")
def get_tender_single(tender_id: str):
    """
    Method to GET the tender record for the supplied id
    """
    get_tender_sql = SQL("""
        SELECT
            t.id
            ,t.tender_title
            ,t.client_id
            ,c.client_name AS client
            ,t.projected_sales_value_gbp
            ,t.date_created
        FROM tender t
        LEFT OUTER JOIN client c
            ON t.client_id = c.id
        WHERE t.id = %s
    """)

    with DatabaseCursor() as cursor:
        cursor.execute(get_tender_sql, [int(tender_id)])
        results = cursor.fetchall()

    return results


@app.get("/tender/titles")
def get_tender_titles() -> list:
    """
    Method to GET all tender titles in the tender table
    Used for populating tender-selection dropdown lists
    """
    get_sql = SQL("""
        SELECT
            id AS tender_id
            ,tender_title
        FROM tender
        ORDER BY tender_title
    """)

    with DatabaseCursor() as cursor:
        cursor.execute(get_sql)
        results = cursor.fetchall()

    return results


@app.post("/tender")
def post_tender(body: Annotated[lax_lists[Tender], Body()]) -> None:
    """POST method for tender table"""
    columns = ("tender_title", "client_id", "projected_sales_value_gbp", "date_created")

    rows = body.root

    logger.info("POST into tender values:")
    logger.info(rows)

    values = [row.model_dump()[column] for column in columns for row in rows]
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
def patch_tender(tender_id: str, body: Annotated[UpdateTender, Body()]) -> None:
    """PATCH method for tender table"""

    logger.info("PATCHing tender ID: %s", tender_id)
    logger.info(app.current_event.body)

    updated_columns = body.model_dump(exclude_unset=True)

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
    """GET method for tenders_services table"""
    max_per_page = 100

    page = app.current_event.query_string_parameters.get("page", 1)
    page = max(int(page), 1)
    per_page = app.current_event.query_string_parameters.get("per_page", 10)
    per_page = min(max(int(per_page), 1), max_per_page)

    offset = per_page * (page - 1)

    get_sql = SQL("""
        WITH filtered_tender_line_items AS (
            SELECT *
            FROM tenders_services
            WHERE tender_id = {tender_id}
        )
        SELECT
            ft.tender_id
            ,t.tender_title
            ,ft.service_id
            ,s.service_name AS service
            ,ft.total_number_pa
            ,ft.unit_price_override_gbp
        FROM filtered_tender_line_items ft
        LEFT OUTER JOIN tender t
            ON ft.tender_id = t.id
        LEFT OUTER JOIN service s
            ON ft.service_id = s.id
        ORDER BY
            ft.tender_id
            ,ft.service_id
        LIMIT {per_page}
        OFFSET {offset}
    """).format(tender_id=tender_id, per_page=per_page, offset=offset)

    with DatabaseCursor() as cursor:
        cursor.execute(get_sql)
        results = cursor.fetchall()

    return results


@app.get("/tender/line-items/rich/<tender_id>")
def get_rich_tender_line_items(tender_id: str) -> list:
    """Enriched GET method for tenders_services table"""
    max_per_page = 100

    page = app.current_event.query_string_parameters.get("page", 1)
    page = max(int(page), 1)
    per_page = app.current_event.query_string_parameters.get("per_page", 10)
    per_page = min(max(int(per_page), 1), max_per_page)

    offset = per_page * (page - 1)

    overhead_recovery_on_labour_cost_gbp = """
        base.labour_cost_gbp * base.overhead_recovery_on_labour_percentage / 100
    """
    fully_absorbed_cost_gbp = f"""
        base.labour_cost_gbp + ({overhead_recovery_on_labour_cost_gbp}) + base.direct_cost_gbp
    """
    profit_margin_gbp = f"""
        ({fully_absorbed_cost_gbp})
        / (1 - (base.required_profit_margin_percentage / 100))
        * (base.required_profit_margin_percentage / 100)
    """
    recommended_unit_price_gbp = f"""
        ({fully_absorbed_cost_gbp}) + ({profit_margin_gbp})
    """
    unit_price_to_use = """
        COALESCE(base.tender_override_unit_price_gbp, base.our_current_unit_price_gbp)
    """
    annual_sales_gbp = f"({unit_price_to_use}) * base.total_number_pa"
    annual_labour_gbp = "base.labour_cost_gbp * base.total_number_pa"
    annual_direct_gbp = "base.direct_cost_gbp * base.total_number_pa"
    annual_overhead_gbp = (
        f"({overhead_recovery_on_labour_cost_gbp}) * base.total_number_pa"
    )
    annual_total_gbp = f"""
        ({annual_labour_gbp}) + ({annual_direct_gbp}) + ({annual_overhead_gbp})
    """
    annual_profit_gbp = f"""
        ({annual_sales_gbp}) - ({annual_total_gbp})
    """

    get_sql = SQL(f"""
        WITH
            tender_line_items_filtered AS (
                SELECT *
                FROM tenders_services
                WHERE tender_id = {{tender_id}}
            )
            ,labour_costs_summed AS (
                SELECT
                    service_id
                    ,SUM(jt.hourly_rate_gbp * lc.required_time_mins / 60)
                        AS total_cost_gbp
                FROM labour_cost lc
                LEFT OUTER JOIN job_title jt
                    ON lc.title_engaged_id = jt.id
                GROUP BY service_id
            )
            ,direct_costs_summed AS (
                SELECT
                    service_id
                    ,SUM(cost_gbp) AS total_cost_gbp
                FROM direct_cost
                GROUP BY service_id
            )
            ,base AS (
                SELECT
                    ft.tender_id
                    ,t.tender_title
                    ,s.category AS service_category
                    ,ft.service_id
                    ,s.service_name AS service
                    ,ft.total_number_pa
                    ,lc.total_cost_gbp AS labour_cost_gbp
                    ,200 AS overhead_recovery_on_labour_percentage
                    ,dc.total_cost_gbp AS direct_cost_gbp
                    ,s.required_profit_margin_percentage
                    ,s.our_current_unit_price_gbp
                    ,ft.unit_price_override_gbp AS tender_override_unit_price_gbp
                FROM tender_line_items_filtered ft
                LEFT OUTER JOIN tender t
                    ON ft.tender_id = t.id
                LEFT OUTER JOIN service s
                    ON ft.service_id = s.id
                LEFT OUTER JOIN labour_costs_summed lc
                    ON ft.service_id = lc.service_id
                LEFT OUTER JOIN direct_costs_summed dc
                    ON ft.service_id = dc.service_id
            )
        SELECT
            base.tender_id
            ,base.tender_title
            ,base.service_category
            ,base.service_id
            ,base.service
            ,base.total_number_pa
            ,ROUND(base.labour_cost_gbp, 2) AS unit_labour_cost_gbp
            ,base.overhead_recovery_on_labour_percentage
            ,ROUND({overhead_recovery_on_labour_cost_gbp}, 2)
                AS overhead_recovery_on_labour_cost_gbp
            ,ROUND(base.direct_cost_gbp, 2) AS unit_direct_cost_gbp
            ,ROUND({fully_absorbed_cost_gbp}, 2) AS fully_absorbed_cost_gbp
            ,base.required_profit_margin_percentage
            ,ROUND({profit_margin_gbp}, 2) AS profit_margin_gbp
            ,ROUND({recommended_unit_price_gbp}, 2) AS recommended_unit_price_gbp
            ,base.our_current_unit_price_gbp
            ,base.tender_override_unit_price_gbp
            ,ROUND({annual_sales_gbp}, 2) AS annual_sales_gbp
            ,ROUND({annual_labour_gbp}, 2) AS annual_labour_gbp
            ,ROUND({annual_direct_gbp}, 2) as annual_direct_gbp
            ,ROUND({annual_overhead_gbp}, 2) as annual_overhead_gbp
            ,ROUND({annual_total_gbp}, 2) AS annual_total_gbp
            ,ROUND({annual_profit_gbp}, 2) AS annual_profit_gbp
        FROM base
        ORDER BY
            base.tender_id
            ,base.service_id
        LIMIT {{per_page}}
        OFFSET {{offset}}
    """).format(tender_id=tender_id, per_page=per_page, offset=offset)

    with DatabaseCursor() as cursor:
        cursor.execute(get_sql)
        results = cursor.fetchall()

    return results


@app.post("/tender/line-items")
def post_tender_line_items(body: Annotated[lax_lists[TenderLineItem], Body()]) -> None:
    """POST method for tenders_services table"""

    columns = (
        "tender_id",
        "service_id",
        "total_number_pa",
        "unit_price_override_gbp",
    )

    rows = body.root

    logger.info("POST into tenders_services values:")
    logger.info(rows)

    values = [row.model_dump()[column] for column in columns for row in rows]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO tenders_services ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


@app.patch("/tender/line-items/<tender_id>/<service_id>")
def patch_tender_line_item(
    tender_id: str, service_id: str, body: Annotated[UpdateTenderLineItem, Body()]
) -> None:
    """PATCH method for tenders_services table"""

    logger.info(
        "PATCHing tenders_services ID %s, service ID %s",
        tender_id,
        service_id,
    )
    logger.info(app.current_event.body)

    updated_columns = body.model_dump(exclude_unset=True)

    set_parts = []
    values = []
    for col, val in updated_columns.items():
        set_parts.append(SQL("{} = %s").format(Identifier(col)))
        values.append(val)

    patch_sql = SQL("""
        UPDATE tenders_services
        SET {}
        WHERE tender_id = %s
          AND service_id = %s
    """).format(SQL(", ").join(set_parts))

    with DatabaseCursor() as cursor:
        cursor.execute(patch_sql, values + [tender_id, service_id])


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    response = app.resolve(event, context)

    # If Lambda is about to be destroyed, clean up
    if context.get_remaining_time_in_millis() < 100:
        db_manager.close_all()

    return response
