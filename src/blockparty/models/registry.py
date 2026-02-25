"""Pydantic models for the chain registry.

These models represent the merged, deduplicated chain data from all three
explorer provider APIs (Etherscan, Routescan, Blockscout).  They are
serialized to/from the bundled ``chains.json`` snapshot.
"""

from __future__ import annotations

from pydantic import BaseModel

from blockparty._types import ExplorerType


class ExplorerInfo(BaseModel):
    """Information about a single explorer backend for a chain.

    Attributes:
        type: The explorer provider (``"etherscan"``, ``"routescan"``, or ``"blockscout"``).
        api_url: Full base URL for API calls (e.g.,
            ``"https://api.etherscan.io/v2/api?chainid=8453"``).
        frontend_url: Generic human-facing explorer URL.  Always present.
        frontend_url_vanity: Vanity hostname URL (Routescan only, when resolved
            via HEAD probe during registry generation).  ``None`` if unavailable.
        status: Etherscan's chain status code (``0`` = offline, ``1`` = ok,
            ``2`` = degraded).  ``None`` for other providers.
        hosted_by: Blockscout's hosting indicator (``"blockscout"`` for
            Blockscout-hosted instances, ``"self"`` for community-hosted).
            ``None`` for other providers.
    """

    type: ExplorerType
    api_url: str
    frontend_url: str
    frontend_url_vanity: str | None = None
    status: int | None = None
    hosted_by: str | None = None


class ChainEntry(BaseModel):
    """A single chain in the registry, with all known explorer backends.

    Attributes:
        chain_id: The EVM chain ID (e.g., ``1`` for Ethereum, ``8453`` for Base).
        name: Human-readable chain name (e.g., ``"Base Mainnet"``).
        is_testnet: Whether this chain is a testnet.
        explorers: All known explorer backends for this chain, in no
            particular order.  Use
            :meth:`~blockparty.registry.ChainRegistry.get_explorer` for
            priority-based selection.
    """

    chain_id: int
    name: str
    is_testnet: bool = False
    explorers: list[ExplorerInfo] = []
