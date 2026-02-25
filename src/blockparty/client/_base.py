"""Shared client logic: response parsing helpers.

Both :class:`AsyncBlockpartyClient` and :class:`SyncBlockpartyClient` use
these functions to parse raw API response dicts into typed Pydantic models.
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from blockparty.backends._base import ExplorerBackend
from blockparty.models.responses import (
    ExplorerResponse,
    InternalTransaction,
    ObjectResponse,
    ScalarResponse,
)

T = TypeVar("T", bound=BaseModel)

# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def _check_error(data: dict[str, Any], backend: ExplorerBackend) -> None:
    """Raise an exception if the API response indicates an error."""
    error = backend.parse_error(data)
    if error is not None:
        raise error


def _coerce_result_list(data: dict[str, Any]) -> list[Any]:
    """Extract result as a list, treating string results as empty."""
    raw = data.get("result", [])
    if isinstance(raw, str):
        return []
    return raw


def parse_internal_tx_response(
    data: dict[str, Any],
    backend: ExplorerBackend,
) -> ExplorerResponse[InternalTransaction]:
    """Parse a raw JSON response into a typed ExplorerResponse.

    Handles backend-specific normalization before Pydantic validation.
    """
    _check_error(data, backend)

    raw_results = _coerce_result_list(data)
    normalized_results = [backend.normalize_internal_tx(item) for item in raw_results]

    return ExplorerResponse[InternalTransaction].model_validate(
        {
            "status": data.get("status"),
            "message": data.get("message", "OK"),
            "result": normalized_results,
        }
    )


def parse_list_response(
    data: dict[str, Any],
    backend: ExplorerBackend,
    model: type[T],
) -> ExplorerResponse[T]:
    """Parse a raw JSON response into a typed ExplorerResponse with list result."""
    _check_error(data, backend)

    raw_results = _coerce_result_list(data)

    return ExplorerResponse[model].model_validate(
        {
            "status": data.get("status"),
            "message": data.get("message", "OK"),
            "result": raw_results,
        }
    )


def parse_scalar_response(
    data: dict[str, Any],
    backend: ExplorerBackend,
) -> ScalarResponse:
    """Parse a raw JSON response whose result is a scalar string."""
    _check_error(data, backend)

    return ScalarResponse.model_validate(
        {
            "status": data.get("status"),
            "message": data.get("message", "OK"),
            "result": str(data.get("result", "")),
        }
    )


def parse_object_response(
    data: dict[str, Any],
    backend: ExplorerBackend,
    model: type[T],
) -> ObjectResponse[T]:
    """Parse a raw JSON response whose result is a single object."""
    _check_error(data, backend)

    return ObjectResponse[model].model_validate(
        {
            "status": data.get("status"),
            "message": data.get("message", "OK"),
            "result": data.get("result", {}),
        }
    )
