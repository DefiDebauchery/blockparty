"""Tests for blockparty._types — hex coercion and CoercedInt."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from blockparty._types import CoercedInt, _coerce_hex_numeric


class TestCoerceHexNumeric:
    def test_hex_string(self):
        assert _coerce_hex_numeric("0xA") == 10

    def test_hex_case_insensitive(self):
        assert _coerce_hex_numeric("0Xff") == 255

    def test_hex_with_whitespace(self):
        assert _coerce_hex_numeric("  0xA  ") == 10

    def test_bare_0x_is_zero(self):
        """APIs return "0x" for zero values in log fields like logIndex."""
        assert _coerce_hex_numeric("0x") == 0

    def test_decimal_string_passthrough(self):
        assert _coerce_hex_numeric("12345") == "12345"

    def test_int_passthrough(self):
        assert _coerce_hex_numeric(42) == 42


class TestCoercedIntInModel:
    """Test CoercedInt through Pydantic validation (the real usage path)."""

    class _M(BaseModel):
        value: CoercedInt

    def test_decimal_string(self):
        assert self._M(value="12345").value == 12345

    def test_hex_string(self):
        assert self._M(value="0xc48174").value == 12_878_196

    def test_int(self):
        assert self._M(value=42).value == 42

    def test_invalid_string_raises(self):
        with pytest.raises(ValidationError):
            self._M(value="not_a_number")
