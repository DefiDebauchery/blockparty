"""Core types and type aliases for blockparty."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BeforeValidator

# ---------------------------------------------------------------------------
# Explorer provider type
# ---------------------------------------------------------------------------

ExplorerType = Literal["etherscan", "routescan", "blockscout"]

EXPLORER_PRIORITY: list[ExplorerType] = ["etherscan", "routescan", "blockscout"]
"""Default resolution order when no explicit explorer_type is specified."""


# ---------------------------------------------------------------------------
# Numeric coercion — extends Pydantic's default str→int with hex support
# ---------------------------------------------------------------------------


def _coerce_hex_numeric(v: str | int) -> int | str:
    """Pre-process hex-encoded numeric strings before Pydantic's built-in coercion.

    Pydantic v2 already handles decimal strings (``"12345"`` → ``12345``) and
    int passthrough natively.  This validator only intercepts hex-prefixed
    strings (``"0x..."``), converting them to ``int`` so Pydantic can accept
    them.  All other values are passed through for Pydantic's default handling
    (which will raise ``ValidationError`` on invalid input like empty strings).

    Args:
        v: The raw value from the API response.

    Returns:
        An ``int`` if hex was detected, otherwise the original value unchanged.
    """
    if isinstance(v, str) and v.strip().startswith(("0x", "0X")):
        digits = v.strip()[2:]
        return int(digits, 16) if digits else 0
    return v


CoercedInt = Annotated[int, BeforeValidator(_coerce_hex_numeric)]
"""An ``int`` that additionally handles hex-encoded strings (``"0x..."``).

Decimal strings and int passthrough are handled by Pydantic's built-in
coercion.  This type adds support for hex strings commonly returned by
``eth_*`` proxy endpoints.
"""
