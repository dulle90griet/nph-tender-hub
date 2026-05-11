# import json
import logging
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck

# import src.lambdas.http_api
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
)

logger.setLevel(logging.ERROR)

settings.register_profile(
    "this_module",
    parent=settings.get_profile("default"),
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
settings.load_profile("this_module")


# ───────────────────────── fixtures ────────────────────────


@pytest.fixture
def mock_cursor():
    """Patch DatabaseCursor and yield a MagicMock cursor that returns [] by default."""
    with patch("src.lambdas.http_api.DatabaseCursor") as mock:
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        mock.return_value.__enter__.return_value = cursor
        mock.return_value.__exit__.return_value = False
        yield cursor


@pytest.fixture
def set_current_event(monkeypatch):
    """Set app.current_event to an empty mock (query params = {}, no body)."""
    event = MagicMock()
    event.query_string_parameters = {}
    event.body = None
    app.current_event = event


@pytest.fixture(autouse=True)
def _auto_set_event(set_current_event):
    """All unit tests get a default empty current_event (harmless for handlers that ignore it)."""
    pass


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


# ───────────────── GET handlers (universal) ─────────────────

# All GET handlers that take NO path parameters
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


class TestGetHandlersReturnCursorRows:
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
    def test_returns_all_cursor_rows(self, mock_cursor, handler, rows):
        mock_cursor.fetchall.return_value = rows
        assert handler() == rows
