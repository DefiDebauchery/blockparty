"""Etherscan backend.

Etherscan uses a unified API gateway at ``api.etherscan.io/v2/api`` with
``chainid`` as a query parameter.  API key is required (``apikey`` param).
Response fields match the canonical format — no normalization needed.
Error parsing follows the standard ``status=0`` convention.
"""

from __future__ import annotations

from blockparty._types import ExplorerType
from blockparty.backends._base import ExplorerBackendBase


class EtherscanBackend(ExplorerBackendBase):
    """Etherscan explorer backend.

    Inherits all shared behaviour from :class:`ExplorerBackendBase` —
    param building, passthrough normalization, and ``status=0`` error parsing.
    """

    @property
    def name(self) -> ExplorerType:
        return "etherscan"
