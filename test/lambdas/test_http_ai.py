# import json
from datetime import datetime
from decimal import Decimal
# from unittest.mock import MagicMock

import pytest

# import src.lambdas.http_api
from src.lambdas.http_api import (
    CustomJSONEncoder,
)


# ──────────────────── CustomJSONEncoder ────────────────────

class TestCustomJSONEncoder:
    @pytest.mark.parametrize("value,expected", [
        (Decimal("10.50"), "10.50"),
        (Decimal("0.00"), "0.00"),
        (Decimal("-5.5"), "-5.5"),
    ])
    def test_serializes_decimal(self, value, expected):
        assert CustomJSONEncoder().default(value) == expected

    @pytest.mark.parametrize("dt", [
        datetime(2026, 5, 6, 12, 0, 0),
        datetime(1999, 1, 1, 0, 0, 0, microsecond=123456),
    ])
    def test_serializes_datetime(self, dt):
        assert CustomJSONEncoder().default(dt) == str(dt)

    def test_raises_typeerror_for_unknown(self):
        with pytest.raises(TypeError):
            CustomJSONEncoder().default(object())
