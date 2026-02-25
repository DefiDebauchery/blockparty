"""Shared error-parsing logic for explorer backends.

All three providers use similar error response patterns (``status=0``,
error details in ``message``/``result``).  This module centralizes the
pattern-matching so each backend doesn't duplicate it.
"""

from __future__ import annotations

import re

from blockparty.exceptions import (
    ChainNotSupportedError,
    ExplorerAPIError,
    InvalidAddressError,
    InvalidAPIKeyError,
    PremiumEndpointError,
    RateLimitError,
)

# Pre-compiled patterns for error classification.
# Order matters — first match wins.
_ERROR_PATTERNS: list[tuple[re.Pattern[str], type[ExplorerAPIError]]] = [
    (re.compile(r"invalid api key|missing.+api key", re.IGNORECASE), InvalidAPIKeyError),
    (re.compile(r"max rate limit|rate limit", re.IGNORECASE), RateLimitError),
    (re.compile(r"invalid address", re.IGNORECASE), InvalidAddressError),
    (re.compile(r"api pro endpoint", re.IGNORECASE), PremiumEndpointError),
    (re.compile(r"not supported for this chain", re.IGNORECASE), ChainNotSupportedError),
]


def classify_error(message: str, result: str | None) -> ExplorerAPIError:
    """Classify an error response into a typed exception.

    Examines both the ``message`` and ``result`` fields from the API response
    against known patterns.  Returns the most specific exception type possible,
    falling back to :class:`ExplorerAPIError` if no pattern matches.

    Args:
        message: The ``message`` field from the response (e.g., ``"NOTOK"``).
        result: The ``result`` field from the response, if it's a string
            (error responses often put the detail here).

    Returns:
        An instance of the appropriate :class:`ExplorerAPIError` subclass.
    """
    # Combine message and result for pattern matching
    search_text = message
    if result:
        search_text = f"{message} {result}"

    for pattern, exc_class in _ERROR_PATTERNS:
        if pattern.search(search_text):
            return exc_class(message, result)

    return ExplorerAPIError(message, result)
