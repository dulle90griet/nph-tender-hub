# import json
from datetime import datetime
from decimal import Decimal
# from unittest.mock import MagicMock

import pytest

# import src.lambdas.http_api
from src.lambdas.http_api import (
    CustomJSONEncoder,
)


# ---------- CustomJSONEncoder ----------

class TestCustomJSONEncoder:
    def test_serializes_decimal(self):
        assert CustomJSONEncoder().default(Decimal("10.50")) == "10.50"

    def test_serializes_datetime(self):
        dt = datetime(2026, 5, 6, 12, 0, 0)
        assert CustomJSONEncoder().default(dt) == str(datetime(2026, 5, 6, 12, 0, 0))

    def test_raises_typeerror_for_unknown(self):
        with pytest.raises(TypeError):
            CustomJSONEncoder().default(object())
