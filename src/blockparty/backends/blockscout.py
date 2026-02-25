"""Blockscout backend.

Blockscout uses per-chain hostnames (e.g., ``base.blockscout.com``) and an
Etherscan-compatible API at ``{host}/api``.  API key is optional.

Key differences from Etherscan/Routescan:
- ``transactionHash`` instead of ``hash``
- ``callType`` instead of ``type`` (though ``type`` is also often present)
- No top-level ``status`` field in responses
- Rate limit info via ``X-Ratelimit-*`` response headers
- ``index`` field present (not ``traceId``)
"""

from __future__ import annotations

from typing import Any

from blockparty._types import ExplorerType
from blockparty.backends._base import ExplorerBackendBase
from blockparty.backends._errors import classify_error
from blockparty.exceptions import ExplorerAPIError


class BlockscoutBackend(ExplorerBackendBase):
    """Blockscout explorer backend.

    Inherits shared param building from :class:`ExplorerBackendBase` but
    overrides normalization (field remapping) and error parsing (Blockscout
    does not use the ``status=0`` convention).
    """

    @property
    def name(self) -> ExplorerType:
        return "blockscout"

    def normalize_internal_tx(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Remap Blockscout-specific field names to the canonical schema.

        - ``transactionHash`` → ``hash`` (if ``hash`` not already present)
        - ``callType`` → ``type`` (if ``type`` not already present)
        """
        normalized = dict(raw)

        if "transactionHash" in normalized and "hash" not in normalized:
            normalized["hash"] = normalized.pop("transactionHash")

        if "callType" in normalized and "type" not in normalized:
            normalized["type"] = normalized["callType"]

        return normalized

    def parse_error(self, response_data: dict[str, Any]) -> ExplorerAPIError | None:
        """Parse errors from Blockscout responses.

        Blockscout does not use a top-level ``status`` field.  Instead,
        success is indicated by ``message="OK"`` or ``result`` being a
        list.  Everything else is treated as an error and classified via
        :func:`~blockparty.backends._errors.classify_error`.
        """
        message = response_data.get("message", "")
        result = response_data.get("result", "")

        # Success conditions.
        if message == "OK" or isinstance(result, list):
            return None

        result_str = result if isinstance(result, str) else None

        # Only treat as error if message is clearly an error indicator.
        if message and message != "OK":
            return classify_error(message, result_str)

        return None
