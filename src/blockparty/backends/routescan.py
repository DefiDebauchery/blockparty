"""Routescan backend.

Routescan uses an Etherscan-compatible API with the chain ID baked into the
URL path: ``api.routescan.io/v2/network/{net}/evm/{chain_id}/etherscan/api``.
API key is optional.  Response format and error conventions match Etherscan.
"""

from __future__ import annotations

from blockparty._types import ExplorerType
from blockparty.backends._base import ExplorerBackendBase


class RoutescanBackend(ExplorerBackendBase):
    """Routescan explorer backend.

    Inherits all shared behaviour from :class:`ExplorerBackendBase` —
    param building, passthrough normalization, and ``status=0`` error parsing.
    """

    @property
    def name(self) -> ExplorerType:
        return "routescan"
