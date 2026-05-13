import json
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
    get_consumable,
    get_consumable_names,
    get_service,
    get_service_slugs,
    get_overhead_cost,
    get_labour_cost,
    get_direct_cost,
    get_client,
    get_tender,
    get_tender_line_items,
    get_rich_tender_line_items,
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


# ── Fixtures ──────────────────────────────────────────────────────
@pytest.fixture
def mock_cursor():
    """Patch DatabaseCursor; yield a fresh MagicMock cursor each test."""
    with patch("src.lambdas.http_api.DatabaseCursor") as mock:
        cursor = MagicMock()
        cursor.fetchall.return_value = []
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


# ══════════════════════════════════════════════════════════════════
# 0. Serialization safety tests
# ══════════════════════════════════════════════════════════════════
class TestHandlerOutputSerializable:
    """Every GET handler must return output that can be serialized by CustomJSONEncoder."""

    def test_department_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {"id": 1, "name": "Engineering"},
            {"id": 2, "name": "A" * 50},  # max varchar(50)
        ]
        result = get_department()
        json.dumps(result, cls=CustomJSONEncoder)

    def test_job_title_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "department": "Eng",
                "title": "Dev",
                "default_ft_weekly_hours": Decimal("37.5"),
                "default_lunch_break_hours": Decimal("0.5"),
                "hourly_rate_gbp": Decimal("50.00"),
                "default_annual_holiday_days": Decimal("25.0"),
                "default_annual_training_days": Decimal("5.0"),
                "default_annual_sick_days": Decimal("3.0"),
            },
        ]
        result = get_job_title()
        json.dumps(result, cls=CustomJSONEncoder)

    def test_job_title_titles_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {"id": 1, "title": "A" * 50},  # max varchar(50)
        ]
        result = get_job_title_titles()
        json.dumps(result, cls=CustomJSONEncoder)

    def test_consumable_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "consumable_name": "Widget",
                "default_unit_cost_gbp": Decimal("9999.99"),
            },  # near max decimal(6,2)
        ]
        result = get_consumable()
        json.dumps(result, cls=CustomJSONEncoder)

    def test_consumable_names_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {"id": 1, "consumable_name": "A" * 100},  # max varchar(100)
        ]
        result = get_consumable_names()
        json.dumps(result, cls=CustomJSONEncoder)

    def test_service_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "pillar": "Tech",
                "category": "Dev",
                "service_name": "Svc",
                "xero_code": 999999,
                "overhead_recovery_on_labour_percentage": 200,
                "required_profit_margin_percentage": Decimal("99.99"),
                "acceptable_market_price_gbp": Decimal("99999999.99"),
                "our_current_unit_price_gbp": Decimal("99999999.99"),
                "new_unit_price_gbp": None,
                "new_day_rate_gbp": None,
                "comments": None,
            },
        ]
        result = get_service()
        json.dumps(result, cls=CustomJSONEncoder)

    def test_service_slugs_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {
                "service_id": 1,
                "service_slug": "A" * 50 + ": " + "B" * 75,
            },  # max varchar(50) + ": " + max varchar(75)
        ]
        result = get_service_slugs()
        json.dumps(result, cls=CustomJSONEncoder)

    def test_overhead_cost_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "cost_type": "Rent",
                "cost_description": "Office",
                "budgeted_spend_gbp": 2147483647,
            },
        ]
        result = get_overhead_cost()
        json.dumps(result, cls=CustomJSONEncoder)

    def test_labour_cost_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {
                "service_id": 1,
                "service": "Svc",
                "title_engaged_id": 2,
                "title_engaged": "Dev",
                "required_time_mins": 480,
            },
        ]
        result = get_labour_cost()
        json.dumps(result, cls=CustomJSONEncoder)

    def test_direct_cost_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {
                "service_id": 1,
                "service": "Svc",
                "consumable_id": 2,
                "consumable": "Widget",
                "cost_gbp": Decimal("999.99"),
            },  # max decimal(5,2)
        ]
        result = get_direct_cost()
        json.dumps(result, cls=CustomJSONEncoder)

    def test_client_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {"id": 1, "client_name": "A" * 50},  # max varchar(50)
        ]
        result = get_client()
        json.dumps(result, cls=CustomJSONEncoder)

    def test_tender_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "tender_title": "T",
                "client_id": 1,
                "client": "Acme",
                "projected_sales_value_gbp": 2147483647,
                "date_created": datetime(2026, 5, 6, 12, 0, 0),
            },
        ]
        result = get_tender()
        json.dumps(result, cls=CustomJSONEncoder)

    def test_tender_line_items_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {
                "tender_id": 1,
                "tender_title": "T",
                "service_id": 2,
                "service": "Svc",
                "total_number_pa": 999999,
                "unit_price_override_gbp": Decimal("99999999.99"),
            },
        ]
        result = get_tender_line_items("1")
        json.dumps(result, cls=CustomJSONEncoder)

    def test_rich_tender_line_items_serializable(self, mock_cursor):
        mock_cursor.fetchall.return_value = [
            {
                "tender_id": 1,
                "tender_title": "T",
                "service_category": "Dev",
                "service_id": 2,
                "service": "Svc",
                "total_number_pa": 100,
                "unit_labour_cost_gbp": "80.00",
                "overhead_recovery_on_labour_percentage": 200,
                "overhead_recovery_on_labour_cost_gbp": "160.00",
                "unit_direct_cost_gbp": "100.00",
                "fully_absorbed_cost_gbp": "340.00",
                "required_profit_margin_percentage": Decimal("30.00"),
                "profit_margin_gbp": "145.71",
                "recommended_unit_price_gbp": "485.71",
                "our_current_unit_price_gbp": Decimal("150.00"),
                "tender_override_hourly_price_gbp": Decimal("200.00"),
                "annual_sales_gbp": "20000.00",
                "annual_labour_gbp": "8000.00",
                "annual_direct_gbp": "10000.00",
                "annual_overhead_gbp": "16000.00",
                "annual_total_gbp": "34000.00",
                "annual_profit_gbp": "-14000.00",
            },
        ]
        result = get_rich_tender_line_items("1")
        json.dumps(result, cls=CustomJSONEncoder)


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
    def test_returns_all_cursor_rows(self, mock_cursor, handler, rows):
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
