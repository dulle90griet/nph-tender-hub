import json
import re
import logging
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, example, settings, HealthCheck
from hypothesis import strategies as st

from src.lambdas.http_api import (
    logger,
    app,
    CustomJSONEncoder,
    get_department,
    get_job_title,
    get_job_title_titles,
    post_job_title,
    patch_job_title,
    get_consumable,
    get_consumable_names,
    post_consumable,
    patch_consumable,
    get_service,
    get_service_slugs,
    post_service,
    patch_service,
    get_overhead_cost,
    post_overhead_cost,
    patch_overhead_cost,
    get_labour_cost,
    post_labour_cost,
    patch_labour_cost,
    get_direct_cost,
    post_direct_cost,
    patch_direct_cost,
    get_client,
    post_client,
    patch_client,
    get_tender,
    post_tender,
    patch_tender,
    get_tender_line_items,
    get_rich_tender_line_items,
    post_tender_line_items,
    patch_tender_line_item,
)

logger.setLevel(logging.ERROR)


# ── Module-level Hypothesis profile ──────────────────────────────
settings.register_profile(
    "this_module",
    parent=settings.get_profile("default"),
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
settings.load_profile("this_module")


# ── Constants ─────────────────────────────────────────────────────
GET_HANDLERS_NO_PATH = [
    get_department,
    get_job_title,
    get_job_title_titles,
    get_consumable,
    get_consumable_names,
    get_service,
    get_service_slugs,
    get_overhead_cost,
    get_labour_cost,
    get_direct_cost,
    get_client,
    get_tender,
]

ALL_POST_HANDLERS = [
    (
        post_job_title,
        "/job-title",
        {
            "department_id": 1,
            "title": "Dev",
            "default_ft_weekly_hours": Decimal("37.5"),
            "default_lunch_break_hours": Decimal("0.5"),
            "hourly_rate_gbp": Decimal("50.00"),
            "default_annual_holiday_days": 30,
            "default_annual_training_days": 15,
            "default_annual_sick_days": 10,
        },
    ),
    (
        post_consumable,
        "/consumable",
        {"consumable_name": "Widget", "default_unit_cost_gbp": Decimal("9.99")},
    ),
    (
        post_service,
        "/service",
        {
            "pillar": "Tech",
            "category": "Dev",
            "service_name": "Svc",
            "xero_code": 1,
            "overhead_recovery_on_labour_percentage": 200,
            "required_profit_margin_percentage": Decimal("30.00"),
            "acceptable_market_price_gbp": Decimal("500.00"),
            "our_current_unit_price_gbp": Decimal("300.00"),
            "new_unit_price_gbp": Decimal("450.00"),
            "new_day_rate_gbp": None,
            "comments": None,
        },
    ),
    (
        post_overhead_cost,
        "/overhead-cost",
        {
            "cost_type": "Rent",
            "cost_description": "Office",
            "budgeted_spend_gbp": 12000,
        },
    ),
    (
        post_labour_cost,
        "/labour-cost",
        {"service_id": 1, "title_engaged_id": 2, "required_time_mins": 30},
    ),
    (
        post_direct_cost,
        "/direct-cost",
        {"service_id": 1, "consumable_id": 2, "cost_gbp": Decimal("12.50")},
    ),
    (
        post_client,
        "/client",
        {"client_name": "Acme Corp"},
    ),
    (
        post_tender,
        "/tender",
        {
            "tender_title": "Big Project",
            "client_id": 1,
            "projected_sales_value_gbp": 75000,
            "date_created": "2026-05-06T12:00:00",
        },
    ),
    (
        post_tender_line_items,
        "/tender/line-items",
        {
            "tender_id": 1,
            "service_id": 2,
            "total_number_pa": 500,
            "unit_price_override_gbp": Decimal("99.95"),
        },
    ),
]

ALL_PATCH_HANDLERS_SINGLE_PATCH = [
    (
        patch_job_title,
        "/job-title/42",
        ("42",),
        {"title": "New"},
    ),
    (
        patch_consumable,
        "/consumable/7",
        ("7",),
        {"default_unit_cost_gbp": 1},
    ),
    (
        patch_service,
        "/service/1",
        ("1",),
        {"service_name": "New"},
    ),
    (
        patch_overhead_cost,
        "/overhead-cost/1",
        ("1",),
        {"budgeted_spend_gbp": 1},
    ),
    (
        patch_labour_cost,
        "/labour-cost/10/20",
        ("10", "20"),
        {"required_time_mins": 30},
    ),
    (
        patch_direct_cost,
        "/direct-cost/1/2",
        ("1", "2"),
        {"cost_gbp": 1},
    ),
    (
        patch_client,
        "/client/12",
        ("12",),
        {"client_name": "New"},
    ),
    (
        patch_tender,
        "/tender/1",
        ("1",),
        {"projected_sales_value_gbp": 1},
    ),
    (
        patch_tender_line_item,
        "/tender/line-items/1/2",
        ("1", "2"),
        {"total_number_pa": 1},
    ),
]

ALL_PATCH_HANDLERS_MULTI_PATCH = [
    (
        patch_job_title,
        "/job-title/7",
        ("7",),
        {
            "title": "Updated Title",
            "hourly_rate_gbp": Decimal("75.00"),
            "default_annual_holiday_days": 30,
        },
    ),
    (
        patch_service,
        "/service/999",
        ("999",),
        {
            "service_name": "Renamed Service",
            "our_current_unit_price_gbp": Decimal("450.00"),
            "required_profit_margin_percentage": Decimal("25.00"),
        },
    ),
    (
        patch_overhead_cost,
        "/overhead-cost/112",
        ("112",),
        {
            "cost_type": "Utilities",
            "budgeted_spend_gbp": 5000,
        },
    ),
    (
        patch_tender,
        "/tender/56",
        ("56",),
        {
            "tender_title": "Updated Tender",
            "projected_sales_value_gbp": 90000,
            "date_created": "2026-06-01T00:00:00",
        },
    ),
    (
        patch_tender_line_item,
        "/tender/line-items/16/32",
        ("16", "32"),
        {
            "total_number_pa": 750,
            "unit_price_override_gbp": Decimal("150.00"),
        },
    ),
]


# ── Fixtures ──────────────────────────────────────────────────────
@pytest.fixture
def mock_cursor():
    """Patch DatabaseCursor; yield a fresh MagicMock cursor each test."""
    with patch("src.lambdas.http_api.DatabaseCursor") as mock:
        cursor = MagicMock()
        cursor.fetchall.return_value = []

        # Add properties needed by psycopg3 SQL.as_string(Cursor)
        mock_adapters = MagicMock()
        cursor.adapters = mock_adapters
        cursor.connection = None

        mock.return_value.__enter__.return_value = cursor
        mock.return_value.__exit__.return_value = False
        yield cursor


@pytest.fixture(autouse=True)
def set_current_event():
    """Set a clean app.current_event before every test."""
    event = MagicMock()
    event.query_string_parameters = {}
    event.body = None
    app.current_event = event


# ── Helper: case‑/whitespace‑insensitive regex ────────────────────
def assert_sql_contains(sql_str, *phrases, in_order=False):
    """Assert that sql_str (after collapsing whitespace) contains each phrase."""
    collapsed = re.sub(r"\s+", " ", sql_str)
    for phrase in phrases:
        match = re.search(re.escape(phrase), collapsed, re.IGNORECASE)
        assert match, (
            f"{phrase!r} not found in {collapsed}"
            if not in_order
            else f"{phrase!r} not found in expected place in {collapsed}"
        )
        if in_order:
            collapsed = collapsed[match.end() :]


# ══════════════════════════════════════════════════════════════════
# 1. Handler returns exactly what cursor produced
# ══════════════════════════════════════════════════════════════════
class TestGetHandlersReturnCursorRows:
    """Property: every GET handler returns exactly what the cursor produced."""

    @pytest.mark.parametrize("handler", GET_HANDLERS_NO_PATH)
    @given(
        rows=st.lists(
            st.dictionaries(
                keys=st.text(min_size=1, max_size=50),
                values=st.none()
                | st.booleans()
                | st.integers()
                | st.floats(allow_nan=False)
                | st.text(max_size=200),
            ),
            min_size=0,
            max_size=200,
        )
    )
    @settings(max_examples=50)
    @example(rows=[])
    def test_all_cursor_rows_returned(self, mock_cursor, handler, rows):
        mock_cursor.fetchall.return_value = rows
        orig_rows = deepcopy(rows)
        assert handler() == orig_rows

    @pytest.mark.parametrize(
        "handler, rows",
        [
            (get_department, [{"id": 1, "name": "A" * 50}]),
            (
                get_job_title,
                [{"id": 1, "title": "A" * 50, "hourly_rate_gbp": Decimal("99999.99")}],
            ),
            (get_job_title_titles, [{"id": 1, "title": "A" * 50}]),
            (get_consumable, [{"id": 1, "default_unit_cost_gbp": Decimal("9999.99")}]),
            (get_consumable_names, [{"id": 1, "consumable_name": "A" * 100}]),
            (
                get_service,
                [{"id": 1, "required_profit_margin_percentage": Decimal("100.00")}],
            ),
            (
                get_service_slugs,
                [{"service_id": 1, "service_slug": "A" * 50 + ": " + "B" * 75}],
            ),
            (get_overhead_cost, [{"id": 1, "budgeted_spend_gbp": 2147483647}]),
            (get_labour_cost, [{"service_id": 1, "required_time_mins": 0}]),
            (get_direct_cost, [{"service_id": 1, "cost_gbp": Decimal("999.99")}]),
            (get_client, [{"id": 1, "client_name": "A" * 50}]),
            (
                get_tender,
                [
                    {
                        "id": 1,
                        "projected_sales_value_gbp": 2147483647,
                        "date_created": datetime(2026, 1, 1),
                    }
                ],
            ),
        ],
    )
    def test_returns_all_cursor_rows_in_boundary_cases(
        self, mock_cursor, handler, rows
    ):
        """Each handler handles schema-limit values without error."""
        mock_cursor.fetchall.return_value = rows
        orig_rows = deepcopy(rows)
        assert handler() == orig_rows

    @pytest.mark.parametrize("tender_id", ["5", "1", "999"])
    @given(
        rows=st.lists(
            st.dictionaries(
                keys=st.text(), values=st.none() | st.integers() | st.text()
            ),
            min_size=0,
            max_size=50,
        )
    )
    @settings(max_examples=50)
    @example(rows=[])
    def test_tender_line_items_returns_all_rows(self, mock_cursor, tender_id, rows):
        mock_cursor.fetchall.return_value = rows
        orig_rows = deepcopy(rows)
        assert get_tender_line_items(tender_id) == orig_rows

    def test_tender_line_items_boundary_case(self, mock_cursor):
        rows = [
            {
                "tender_id": 1,
                "tender_title": "T" * 50,
                "service_id": 2,
                "service": "S" * 75,
                "total_number_pa": 999999,
                "unit_price_override_gbp": Decimal("999999.99"),
            }
        ]
        orig_rows = deepcopy(rows)
        mock_cursor.fetchall.return_value = rows
        assert get_tender_line_items(1) == orig_rows

    @pytest.mark.parametrize("tender_id", ["1", "42"])
    @given(
        rows=st.lists(
            st.dictionaries(
                keys=st.text(), values=st.none() | st.integers() | st.text()
            ),
            min_size=0,
            max_size=20,
        )
    )
    @settings(max_examples=50)
    @example(rows=[])
    def test_rich_tender_line_items_returns_all_rows(
        self, mock_cursor, tender_id, rows
    ):
        mock_cursor.fetchall.return_value = rows
        orig_rows = deepcopy(rows)
        assert get_rich_tender_line_items(tender_id) == orig_rows

    def test_rich_tender_line_items_boundary_case(self, mock_cursor):
        rows = [
            {
                "tender_id": 1,
                "tender_title": "A" * 50,
                "service_category": "A" * 50,
                "service_id": 2147483647,
                "service": "A" * 75,
                "total_number_pa": 2147483647,
                "unit_labour_cost_gbp": Decimal("999999.99"),
                "overhead_recovery_on_labour_percentage": 2147483647,
                "overhead_recovery_on_labour_cost_gbp": Decimal("999999.99"),
                "unit_direct_cost_gbp": Decimal("999.99"),
                "fully_absorbed_cost_gbp": Decimal("999999.99"),
                "required_profit_margin_percentage": Decimal("99.99"),
                "profit_margin_gbp": Decimal("999999.99"),
                "recommended_unit_price_gbp": Decimal("999999.99"),
                "our_current_unit_price_gbp": Decimal("999999.99"),
                "tender_override_hourly_price_gbp": Decimal("999999.99"),
                "annual_sales_gbp": Decimal("10000000000.00"),
                "annual_labour_gbp": Decimal("10000000000.00"),
                "annual_direct_gbp": Decimal("10000000000.00"),
                "annual_overhead_gbp": Decimal("10000000000.00"),
                "annual_total_gbp": Decimal("10000000000.00"),
                "annual_profit_gbp": Decimal("-10000000000.00"),
            }
        ]
        orig_rows = deepcopy(rows)
        mock_cursor.fetchall.return_value = rows
        assert get_rich_tender_line_items(1) == rows


# ══════════════════════════════════════════════════════════════════
# 2. Pagination clamping
# ══════════════════════════════════════════════════════════════════
class TestPaginationClamping:
    @pytest.mark.parametrize(
        "handler, page, per_page, expected_page, expected_limit",
        [
            # get_job_title
            (get_job_title, -5, 10, 1, 10),
            (get_job_title, 1, -5, 1, 1),
            (get_job_title, 1, 10, 1, 10),
            (get_job_title, 1, 200, 1, 100),
            (get_job_title, -3, 400, 1, 100),
            # get_consumable
            (get_consumable, -1, 15, 1, 15),
            (get_consumable, 1, -1, 1, 1),
            (get_consumable, 2, 15, 2, 15),
            (get_consumable, 1, 500, 1, 100),
            (get_consumable, -5, 300, 1, 100),
            # get_service
            (get_service, -99, 50, 1, 50),
            (get_service, 2, -99, 2, 1),
            (get_service, 3, 50, 3, 50),
            (get_service, 2, 101, 2, 100),
            (get_service, -2, 100000, 1, 100),
            # get_overhead_cost
            (get_overhead_cost, -3, 10, 1, 10),
            (get_overhead_cost, 3, -3, 3, 1),
            (get_overhead_cost, 4, 10, 4, 10),
            (get_overhead_cost, 3, 99999, 3, 100),
            (get_overhead_cost, -9, 999, 1, 100),
            # get_labour_cost
            (get_labour_cost, -7, 20, 1, 20),
            (get_labour_cost, 1, -7, 1, 1),
            (get_labour_cost, 1, 20, 1, 20),
            (get_labour_cost, 1, 150, 1, 100),
            (get_labour_cost, -20, 101, 1, 100),
            # get_direct_cost
            (get_direct_cost, -2, 5, 1, 5),
            (get_direct_cost, 2, -2, 2, 1),
            (get_direct_cost, 5, 5, 5, 5),
            (get_direct_cost, 2, 200, 2, 100),
            (get_direct_cost, -10, 800, 1, 100),
            # get_client
            (get_client, -10, 100, 1, 100),
            (get_client, 1, -10, 1, 1),
            (get_client, 2, 100, 2, 100),
            (get_client, 1, 1000, 1, 100),
            (get_client, -80, 170, 1, 100),
            # get_tender
            (get_tender, -1, 10, 1, 10),
            (get_tender, 3, -1, 3, 1),
            (get_tender, 10, 10, 10, 10),
            (get_tender, 3, 250, 3, 100),
            (get_tender, -700, 10000, 1, 100),
        ],
    )
    def test_pagination_clamped(
        self, mock_cursor, handler, page, per_page, expected_page, expected_limit
    ):
        app.current_event.query_string_parameters = {
            "page": str(page),
            "per_page": str(per_page),
        }
        handler()
        sql = mock_cursor.execute.call_args[0][0].as_string()
        expected_offset = expected_limit * (expected_page - 1)
        assert_sql_contains(sql, f"LIMIT {expected_limit}", f"OFFSET {expected_offset}")


# ══════════════════════════════════════════════════════════════════
# 3. Handlers call cursor.execute the expected number of times
# ══════════════════════════════════════════════════════════════════
class TestHandlersCallExecuteOnce:
    """Every handler must call cursor.execute exactly once."""

    # ── GET handlers ──────────────────────────────────────────

    @pytest.mark.parametrize("handler", GET_HANDLERS_NO_PATH)
    def test_get_handlers_call_execute_once(self, mock_cursor, handler):
        handler()
        assert mock_cursor.execute.call_count == 1

    @pytest.mark.parametrize("tender_id", ["1", "42"])
    def test_get_tender_line_items_calls_execute_once(self, mock_cursor, tender_id):
        get_tender_line_items(tender_id)
        assert mock_cursor.execute.call_count == 1

    @pytest.mark.parametrize("tender_id", ["5", "999"])
    def test_get_rich_tender_line_items_calls_execute_once(
        self, mock_cursor, tender_id
    ):
        get_rich_tender_line_items(tender_id)
        assert mock_cursor.execute.call_count == 1

    # ── POST handlers ─────────────────────────────────────────

    @pytest.mark.parametrize("handler, _, body", ALL_POST_HANDLERS)
    def test_post_handlers_call_execute_once(self, mock_cursor, handler, _, body):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        handler()
        assert mock_cursor.execute.call_count == 1

    # ── PATCH handlers ────────────────────────────────────────

    @pytest.mark.parametrize(
        "handler, _, path_args, body",
        ALL_PATCH_HANDLERS_SINGLE_PATCH + ALL_PATCH_HANDLERS_MULTI_PATCH,
    )
    def test_patch_handler_calls_execute_once(
        self, mock_cursor, handler, _, path_args, body
    ):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        handler(*path_args)
        assert mock_cursor.execute.call_count == 1


# ══════════════════════════════════════════════════════════════════
# 5. POST/PATCH SQL reflects request body as expected
# ══════════════════════════════════════════════════════════════════
class TestPostHandlersSQLReflectsParams:
    # ── POST /job-title ─────────────────────────────────────
    @pytest.mark.parametrize(
        "body, expected_params",
        [
            (
                {
                    "department_id": 1,
                    "title": "Dev",
                    "default_ft_weekly_hours": "37.5",
                    "default_lunch_break_hours": "0.5",
                    "hourly_rate_gbp": "50.00",
                    "default_annual_holiday_days": None,
                    "default_annual_training_days": None,
                    "default_annual_sick_days": None,
                },
                [
                    1,
                    "Dev",
                    "37.5",
                    "0.5",
                    "50.00",
                    None,
                    None,
                    None,
                ],
            ),
            (
                {
                    "department_id": 2,
                    "title": "QA",
                    "default_ft_weekly_hours": "40.0",
                    "default_lunch_break_hours": "1.0",
                    "hourly_rate_gbp": "45.00",
                    "default_annual_holiday_days": 28,
                    "default_annual_training_days": 3,
                    "default_annual_sick_days": 5,
                },
                [2, "QA", "40.0", "1.0", "45.00", 28, 3, 5],
            ),
        ],
    )
    def test_post_job_title_insert_values(self, mock_cursor, body, expected_params):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        post_job_title()
        assert mock_cursor.execute.call_args[0][1] == expected_params

    # ── POST /consumable ──────────────────────────────────────
    @pytest.mark.parametrize(
        "body, expected_params",
        [
            (
                {"consumable_name": "Widget", "default_unit_cost_gbp": "9.99"},
                ["Widget", "9.99"],
            ),
            (
                {"consumable_name": "Gadget", "default_unit_cost_gbp": None},
                ["Gadget", None],
            ),
        ],
    )
    def test_post_consumable_insert_values(self, mock_cursor, body, expected_params):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        post_consumable()
        assert mock_cursor.execute.call_args[0][1] == expected_params

    # ── POST /service ─────────────────────────────────────────
    @pytest.mark.parametrize(
        "body, expected_params",
        [
            (
                {
                    "pillar": "Tech",
                    "category": "Dev",
                    "service_name": "Consulting",
                    "xero_code": 100,
                    "overhead_recovery_on_labour_percentage": 200,
                    "required_profit_margin_percentage": "30.00",
                    "acceptable_market_price_gbp": "500.00",
                    "our_current_unit_price_gbp": "300.00",
                    "new_unit_price_gbp": None,
                    "new_day_rate_gbp": None,
                    "comments": None,
                },
                [
                    "Tech",
                    "Dev",
                    "Consulting",
                    100,
                    200,
                    "30.00",
                    "500.00",
                    "300.00",
                    None,
                    None,
                    None,
                ],
            ),
            (
                {
                    "pillar": "Ops",
                    "category": "Support",
                    "service_name": "Helpdesk",
                    "xero_code": 200,
                    "overhead_recovery_on_labour_percentage": 150,
                    "required_profit_margin_percentage": "20.00",
                    "acceptable_market_price_gbp": "200.00",
                    "our_current_unit_price_gbp": "150.00",
                    "new_unit_price_gbp": "175.00",
                    "new_day_rate_gbp": "1400.00",
                    "comments": "Urgent setup",
                },
                [
                    "Ops",
                    "Support",
                    "Helpdesk",
                    200,
                    150,
                    "20.00",
                    "200.00",
                    "150.00",
                    "175.00",
                    "1400.00",
                    "Urgent setup",
                ],
            ),
        ],
    )
    def test_post_service_insert_values(self, mock_cursor, body, expected_params):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        post_service()
        assert mock_cursor.execute.call_args[0][1] == expected_params

    # ── POST /overhead-cost ───────────────────────────────────
    @pytest.mark.parametrize(
        "body, expected_params",
        [
            (
                {
                    "cost_type": "Rent",
                    "cost_description": "Office",
                    "budgeted_spend_gbp": 12000,
                },
                ["Rent", "Office", 12000],
            ),
            (
                {
                    "cost_type": "Utilities",
                    "cost_description": "Electricity Costs (Lighting and Automata)",
                    "budgeted_spend_gbp": 500,
                },
                ["Utilities", "Electricity Costs (Lighting and Automata)", 500],
            ),
        ],
    )
    def test_post_overhead_cost_insert_values(self, mock_cursor, body, expected_params):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        post_overhead_cost()
        assert mock_cursor.execute.call_args[0][1] == expected_params

    # ── POST /labour-cost ─────────────────────────────────────
    @pytest.mark.parametrize(
        "body, expected_params",
        [
            (
                {"service_id": 1, "title_engaged_id": 2, "required_time_mins": 30},
                [1, 2, 30],
            ),
            (
                {"service_id": 10, "title_engaged_id": 20, "required_time_mins": 45},
                [10, 20, 45],
            ),
        ],
    )
    def test_post_labour_cost_insert_values(self, mock_cursor, body, expected_params):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        post_labour_cost()
        assert mock_cursor.execute.call_args[0][1] == expected_params

    # ── POST /direct-cost ─────────────────────────────────────
    @pytest.mark.parametrize(
        "body, expected_params",
        [
            (
                {"service_id": 1, "consumable_id": 2, "cost_gbp": "12.50"},
                [1, 2, "12.50"],
            ),
            (
                {"service_id": 5, "consumable_id": 8, "cost_gbp": "999.99"},
                [5, 8, "999.99"],
            ),
        ],
    )
    def test_post_direct_cost_insert_values(self, mock_cursor, body, expected_params):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        post_direct_cost()
        assert mock_cursor.execute.call_args[0][1] == expected_params

    # ── POST /client ──────────────────────────────────────────
    @pytest.mark.parametrize(
        "body, expected_params",
        [
            ({"client_name": "Acme Corp"}, ["Acme Corp"]),
            (
                {"client_name": "Gridlokkk Holdings Incorporated (and Old Associates)"},
                ["Gridlokkk Holdings Incorporated (and Old Associates)"],
            ),
        ],
    )
    def test_post_client_insert_values(self, mock_cursor, body, expected_params):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        post_client()
        assert mock_cursor.execute.call_args[0][1] == expected_params

    # ── POST /tender ──────────────────────────────────────────
    @pytest.mark.parametrize(
        "body, expected_params",
        [
            (
                {
                    "tender_title": "Big Project",
                    "client_id": 1,
                    "projected_sales_value_gbp": 75000,
                    "date_created": "2026-05-06T12:00:00",
                },
                ["Big Project", 1, 75000, "2026-05-06T12:00:00"],
            ),
            (
                {
                    "tender_title": "Small Project, in Elements Dismayingly Various",
                    "client_id": 3,
                    "projected_sales_value_gbp": 5000,
                    "date_created": "2026-01-01T00:00:00",
                },
                [
                    "Small Project, in Elements Dismayingly Various",
                    3,
                    5000,
                    "2026-01-01T00:00:00",
                ],
            ),
        ],
    )
    def test_post_tender_insert_values(self, mock_cursor, body, expected_params):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        post_tender()
        assert mock_cursor.execute.call_args[0][1] == expected_params

    # ── POST /tender/line-items ──────────────────────────────
    @pytest.mark.parametrize(
        "body, expected_params",
        [
            (
                {
                    "tender_id": 1,
                    "service_id": 2,
                    "total_number_pa": 500,
                    "unit_price_override_gbp": "99.95",
                },
                [1, 2, 500, "99.95"],
            ),
            (
                {
                    "tender_id": 10,
                    "service_id": 20,
                    "total_number_pa": 1000,
                    "unit_price_override_gbp": None,
                },
                [10, 20, 1000, None],
            ),
        ],
    )
    def test_post_tender_line_items_insert_values(
        self, mock_cursor, body, expected_params
    ):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        post_tender_line_items()
        assert mock_cursor.execute.call_args[0][1] == expected_params


class TestPatchHandlersSQLAndParamsReflectBody:
    # ── PATCH /job-title ──────────────────────────────────────
    @pytest.mark.parametrize(
        "path_args, body, expected_sql_phrases, expected_params",
        [
            (
                ("42",),
                {
                    "title": "New Title",
                    "hourly_rate_gbp": "75.00",
                    "default_annual_holiday_days": 30,
                },
                [
                    "UPDATE job_title SET",
                    '"title" =',
                    '"hourly_rate_gbp" =',
                    '"default_annual_holiday_days" =',
                    "WHERE ID = %s",
                ],
                ["New Title", "75.00", 30, 42],
            ),
            (
                ("1",),
                {"title": "R" * 50},
                ["UPDATE job_title SET", '"title" =', "WHERE ID = %s"],
                ["R" * 50, 1],
            ),
        ],
    )
    def test_patch_job_title_sql_and_params(
        self, mock_cursor, path_args, body, expected_sql_phrases, expected_params
    ):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        patch_job_title(*path_args)
        args = mock_cursor.execute.call_args[0]
        assert_sql_contains(
            args[0].as_string(mock_cursor), *expected_sql_phrases, in_order=True
        )
        assert args[1] == expected_params

    # ── PATCH /consumable ─────────────────────────────────────
    @pytest.mark.parametrize(
        "path_args, body, expected_sql_phrases, expected_params",
        [
            (
                ("7",),
                {"default_unit_cost_gbp": "5.00"},
                ["UPDATE consumable SET", '"default_unit_cost_gbp" =', "WHERE ID = %s"],
                ["5.00", 7],
            ),
            (
                ("3",),
                {
                    "consumable_name": "Renamed Item of Many Parts (20 pack incl. nibs, grubs, gauze, fur, application steadiness & hand bands)",
                    "default_unit_cost_gbp": "9999.99",
                },
                [
                    "UPDATE consumable SET",
                    '"consumable_name" =',
                    '"default_unit_cost_gbp" =',
                    "WHERE ID = %s",
                ],
                [
                    "Renamed Item of Many Parts (20 pack incl. nibs, grubs, gauze, fur, application steadiness & hand bands)",
                    "9999.99",
                    3,
                ],
            ),
        ],
    )
    def test_patch_consumable_sql_and_params(
        self, mock_cursor, path_args, body, expected_sql_phrases, expected_params
    ):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        patch_consumable(*path_args)
        args = mock_cursor.execute.call_args[0]
        assert_sql_contains(
            args[0].as_string(mock_cursor), *expected_sql_phrases, in_order=True
        )
        assert args[1] == expected_params

    # ── PATCH /service ────────────────────────────────────────
    @pytest.mark.parametrize(
        "path_args, body, expected_sql_phrases, expected_params",
        [
            (
                ("1",),
                {
                    "service_name": "Updated",
                    "our_current_unit_price_gbp": "450.00",
                    "required_profit_margin_percentage": "25.02",
                },
                [
                    "UPDATE service SET",
                    '"service_name" =',
                    '"our_current_unit_price_gbp" =',
                    '"required_profit_margin_percentage" =',
                    "WHERE ID = %s",
                ],
                ["Updated", "450.00", "25.02", 1],
            ),
            (
                ("99",),
                {"service_name": "S" * 75},
                ["UPDATE service SET", '"service_name" =', "WHERE ID = %s"],
                ["S" * 75, 99],
            ),
        ],
    )
    def test_patch_service_sql_and_params(
        self, mock_cursor, path_args, body, expected_sql_phrases, expected_params
    ):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        patch_service(*path_args)
        args = mock_cursor.execute.call_args[0]
        assert_sql_contains(
            args[0].as_string(mock_cursor), *expected_sql_phrases, in_order=True
        )
        assert args[1] == expected_params

    # ── PATCH /overhead-cost ──────────────────────────────────
    @pytest.mark.parametrize(
        "path_args, body, expected_sql_phrases, expected_params",
        [
            (
                ("1",),
                {
                    "cost_type": "Utilities Outlay (TO RETIRE)",
                    "budgeted_spend_gbp": 5000,
                },
                [
                    "UPDATE overhead_cost SET",
                    '"cost_type" =',
                    '"budgeted_spend_gbp" =',
                    "WHERE ID = %s",
                ],
                ["Utilities Outlay (TO RETIRE)", 5000, 1],
            ),
            (
                ("3",),
                {"budgeted_spend_gbp": 999},
                ["UPDATE overhead_cost SET", '"budgeted_spend_gbp" =', "WHERE ID = %s"],
                [999, 3],
            ),
        ],
    )
    def test_patch_overhead_cost_sql_and_params(
        self, mock_cursor, path_args, body, expected_sql_phrases, expected_params
    ):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        patch_overhead_cost(*path_args)
        args = mock_cursor.execute.call_args[0]
        assert_sql_contains(
            args[0].as_string(mock_cursor), *expected_sql_phrases, in_order=True
        )
        assert args[1] == expected_params

    # ── PATCH /labour-cost ────────────────────────────────────
    @pytest.mark.parametrize(
        "path_args, body, expected_sql_phrases, expected_params",
        [
            (
                ("10", "20"),
                {"required_time_mins": 45},
                [
                    "UPDATE labour_cost SET",
                    "required_time_mins =",
                    "WHERE service_id = %s",
                    "AND title_engaged_id = %s",
                ],
                [45, 10, 20],
            ),
            (
                ("9", "800"),
                {"required_time_mins": 120},
                [
                    "UPDATE labour_cost SET",
                    "required_time_mins =",
                    "WHERE service_id = %s",
                    "AND title_engaged_id = %s",
                ],
                [120, 9, 800],
            ),
        ],
    )
    def test_patch_labour_cost_sql_and_params(
        self, mock_cursor, path_args, body, expected_sql_phrases, expected_params
    ):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        patch_labour_cost(*path_args)
        args = mock_cursor.execute.call_args[0]
        assert_sql_contains(
            args[0].as_string(mock_cursor), *expected_sql_phrases, in_order=True
        )
        assert args[1] == expected_params

    # ── PATCH /direct-cost ────────────────────────────────────
    @pytest.mark.parametrize(
        "path_args, body, expected_sql_phrases, expected_params",
        [
            (
                ("1", "2"),
                {"cost_gbp": "15.00"},
                [
                    "UPDATE direct_cost SET",
                    "cost_gbp =",
                    "WHERE service_id = %s",
                    "AND consumable_id = %s",
                ],
                ["15.00", 1, 2],
            ),
            (
                ("1000", "27"),
                {"cost_gbp": "999.99"},
                [
                    "UPDATE direct_cost SET",
                    "cost_gbp =",
                    "WHERE service_id = %s",
                    "AND consumable_id = %s",
                ],
                ["999.99", 1000, 27],
            ),
        ],
    )
    def test_patch_direct_cost_sql_and_params(
        self, mock_cursor, path_args, body, expected_sql_phrases, expected_params
    ):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        patch_direct_cost(*path_args)
        args = mock_cursor.execute.call_args[0]
        assert_sql_contains(
            args[0].as_string(mock_cursor), *expected_sql_phrases, in_order=True
        )
        assert args[1] == expected_params

    # ── PATCH /client ─────────────────────────────────────────
    @pytest.mark.parametrize(
        "path_args, body, expected_sql_phrases, expected_params",
        [
            (
                ("12",),
                {"client_name": "New Corp"},
                ["UPDATE client SET", "client_name =", "WHERE id = %s"],
                ["New Corp", 12],
            ),
            (
                ("12",),
                {"client_name": "C" * 50},
                ["UPDATE client SET", "client_name =", "WHERE id = %s"],
                ["C" * 50, 12],
            ),
        ],
    )
    def test_patch_client_sql_and_params(
        self, mock_cursor, path_args, body, expected_sql_phrases, expected_params
    ):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        patch_client(*path_args)
        args = mock_cursor.execute.call_args[0]
        assert_sql_contains(
            args[0].as_string(mock_cursor), *expected_sql_phrases, in_order=True
        )
        assert args[1] == expected_params

    # ── PATCH /tender ─────────────────────────────────────────
    @pytest.mark.parametrize(
        "path_args, body, expected_sql_phrases, expected_params",
        [
            (
                ("1",),
                {
                    "tender_title": "New Tender Title, Long In Tooth (Don't Delete!)",
                    "projected_sales_value_gbp": 90000,
                    "date_created": "2026-06-01T00:00:00",
                },
                [
                    "UPDATE tender SET",
                    '"tender_title" =',
                    '"projected_sales_value_gbp" =',
                    '"date_created" =',
                    "WHERE ID = %s",
                ],
                [
                    "New Tender Title, Long In Tooth (Don't Delete!)",
                    90000,
                    "2026-06-01T00:00:00",
                    1,
                ],
            ),
            (
                ("5",),
                {"projected_sales_value_gbp": 80000},
                ["UPDATE tender SET", '"projected_sales_value_gbp" =', "WHERE ID = %s"],
                [80000, 5],
            ),
        ],
    )
    def test_patch_tender_sql_and_params(
        self, mock_cursor, path_args, body, expected_sql_phrases, expected_params
    ):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        patch_tender(*path_args)
        args = mock_cursor.execute.call_args[0]
        assert_sql_contains(
            args[0].as_string(mock_cursor), *expected_sql_phrases, in_order=True
        )
        assert args[1] == expected_params

    # ── PATCH /tender/line-item ───────────────────────────────
    @pytest.mark.parametrize(
        "path_args, body, expected_sql_phrases, expected_params",
        [
            (
                ("1", "2"),
                {
                    "total_number_pa": 750,
                    "unit_price_override_gbp": "123456.78",
                },
                [
                    "UPDATE tenders_services SET",
                    "WHERE tender_id = %s",
                    "AND service_id = %s",
                ],
                [750, "123456.78", "1", "2"],
            ),
            (
                ("99", "100"),
                {"total_number_pa": 25000},
                [
                    "UPDATE tenders_services SET",
                    "WHERE tender_id = %s",
                    "AND service_id = %s",
                ],
                [25000, "99", "100"],
            ),
        ],
    )
    def test_patch_tender_line_item_sql_and_params(
        self, mock_cursor, path_args, body, expected_sql_phrases, expected_params
    ):
        app.current_event.body = json.dumps(body, cls=CustomJSONEncoder)
        patch_tender_line_item(*path_args)
        args = mock_cursor.execute.call_args[0]
        assert_sql_contains(
            args[0].as_string(mock_cursor), *expected_sql_phrases, in_order=True
        )
        assert args[1] == expected_params


# ──────────────────── CustomJSONEncoder ────────────────────
class TestCustomJSONEncoder:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (Decimal("10.50"), "10.50"),
            (Decimal("0.00"), "0.00"),
            (Decimal("-5.5"), "-5.5"),
        ],
    )
    def test_serializes_decimal(self, value, expected):
        assert CustomJSONEncoder().default(value) == expected

    @pytest.mark.parametrize(
        "dt",
        [
            datetime(2026, 5, 6, 12, 0, 0),
            datetime(1999, 1, 1, 0, 0, 0, microsecond=123456),
        ],
    )
    def test_serializes_datetime(self, dt):
        assert CustomJSONEncoder().default(dt) == str(dt)

    def test_raises_typeerror_for_unknown(self):
        with pytest.raises(TypeError):
            CustomJSONEncoder().default(object())
