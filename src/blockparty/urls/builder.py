"""Frontend URL builders for explorer pages.

Constructs human-facing URLs for addresses, transactions, tokens, and blocks
across all three explorer providers.  Routescan URLs prefer vanity hostnames
when available, falling back to the generic pattern.

Usage::

    urls = ExplorerURLs(
        explorer_type="etherscan",
        frontend_url="https://basescan.org/",
    )
    print(urls.address("0x..."))  # https://basescan.org/address/0x...
    print(urls.tx("0x..."))       # https://basescan.org/tx/0x...
"""

from __future__ import annotations

from blockparty._types import ExplorerType


class ExplorerURLs:
    """Build frontend explorer URLs for a specific chain and provider.

    Args:
        explorer_type: The explorer provider.
        frontend_url: The base frontend URL (always present).
        frontend_url_vanity: Vanity hostname URL (Routescan only).
        chain_id: The chain ID (needed for Routescan generic URLs).
        is_testnet: Whether this is a testnet chain.
    """

    __slots__ = (
        "_type",
        "_base",
        "_vanity",
        "_chain_id",
        "_is_testnet",
    )

    def __init__(
        self,
        explorer_type: ExplorerType,
        frontend_url: str,
        frontend_url_vanity: str | None = None,
        chain_id: int | None = None,
        is_testnet: bool = False,
    ) -> None:
        self._type = explorer_type
        self._base = frontend_url.rstrip("/")
        self._vanity = frontend_url_vanity.rstrip("/") if frontend_url_vanity else None
        self._chain_id = chain_id
        self._is_testnet = is_testnet

    def _routescan_url(self, path: str, *, needs_chainid: bool = False) -> str:
        """Build a Routescan URL, preferring vanity when available.

        For ``/block/`` paths, ``chainid`` is always appended (per Routescan docs).
        For other paths, ``chainid`` is only appended on the generic hostname.
        """
        if self._vanity:
            url = f"{self._vanity}{path}"
            if needs_chainid and self._chain_id is not None:
                url += f"?chainid={self._chain_id}"
            return url

        # Generic pattern: routescan.io or testnet.routescan.io
        base = "https://testnet.routescan.io" if self._is_testnet else "https://routescan.io"
        url = f"{base}{path}"
        if self._chain_id is not None:
            url += f"?chainid={self._chain_id}"
        return url

    def address(self, address: str) -> str:
        """URL for an address page."""
        if self._type == "routescan":
            return self._routescan_url(f"/address/{address}")
        return f"{self._base}/address/{address}"

    def tx(self, tx_hash: str) -> str:
        """URL for a transaction page."""
        if self._type == "routescan":
            return self._routescan_url(f"/tx/{tx_hash}")
        return f"{self._base}/tx/{tx_hash}"

    def token(self, token_address: str) -> str:
        """URL for a token page."""
        if self._type == "routescan":
            return self._routescan_url(f"/token/{token_address}")
        return f"{self._base}/token/{token_address}"

    def block(self, block_number: int) -> str:
        """URL for a block page.

        Note: Routescan ``/block/`` always requires ``chainid`` even on vanity hosts.
        """
        if self._type == "routescan":
            return self._routescan_url(f"/block/{block_number}", needs_chainid=True)
        return f"{self._base}/block/{block_number}"

    def blocks(self) -> str:
        """URL for the blocks listing page."""
        if self._type == "routescan":
            return self._routescan_url("/blocks")
        return f"{self._base}/blocks"

    def __repr__(self) -> str:
        return f"ExplorerURLs(type={self._type!r}, base={self._base!r})"
