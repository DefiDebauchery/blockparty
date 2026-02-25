"""Shared test fixtures for blockparty tests.

Provides mock chain registry, mock transport, and helper factories
so that no test requires network access.
"""

from __future__ import annotations

from typing import Any

import pytest

from blockparty.models.registry import ChainEntry, ExplorerInfo
from blockparty.pool._base import ProviderCredential, ProviderSet
from blockparty.ratelimit.tiers import EtherscanTier, RoutescanTier
from blockparty.registry.chain_registry import ChainRegistry

# ---------------------------------------------------------------------------
# Chain registry fixtures
# ---------------------------------------------------------------------------


def _make_chain_entry(
    chain_id: int,
    name: str,
    *,
    etherscan: bool = True,
    routescan: bool = True,
    blockscout: bool = True,
    is_testnet: bool = False,
) -> ChainEntry:
    """Build a ChainEntry with configurable explorer availability."""
    explorers: list[ExplorerInfo] = []
    if etherscan:
        explorers.append(
            ExplorerInfo(
                type="etherscan",
                api_url=f"https://api.etherscan.io/v2/api?chainid={chain_id}",
                frontend_url="https://etherscan.io/",
            )
        )
    if routescan:
        explorers.append(
            ExplorerInfo(
                type="routescan",
                api_url=f"https://api.routescan.io/v2/network/mainnet/evm/{chain_id}/etherscan/api",
                frontend_url="https://routescan.io",
                frontend_url_vanity=f"https://{name.lower()}.routescan.io",
            )
        )
    if blockscout:
        explorers.append(
            ExplorerInfo(
                type="blockscout",
                api_url=f"https://{name.lower()}.blockscout.com/api",
                frontend_url=f"https://{name.lower()}.blockscout.com/",
            )
        )
    return ChainEntry(
        chain_id=chain_id,
        name=name,
        is_testnet=is_testnet,
        explorers=explorers,
    )


@pytest.fixture
def mock_registry() -> ChainRegistry:
    """A ChainRegistry with three test chains, no disk I/O."""
    entries = [
        _make_chain_entry(1, "Ethereum"),
        _make_chain_entry(8453, "Base"),
        _make_chain_entry(42161, "Arbitrum"),
        _make_chain_entry(999, "TestOnly", etherscan=False, routescan=False, blockscout=True),
    ]
    return ChainRegistry(entries)


# ---------------------------------------------------------------------------
# Transport fixtures
# ---------------------------------------------------------------------------


class MockAsyncTransport:
    """In-memory async transport that returns pre-configured responses."""

    def __init__(self) -> None:
        self.responses: dict[str, dict[str, Any]] = {}
        self.calls: list[tuple[str, str, dict[str, str]]] = []
        self.closed = False

    def set_response(self, url_contains: str, data: dict[str, Any]) -> None:
        """Register a response for any URL containing the given substring."""
        self.responses[url_contains] = data

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str],
    ) -> dict[str, Any]:
        self.calls.append((method, url, params))
        for pattern, data in self.responses.items():
            if pattern in url:
                return data
        return {"status": "1", "message": "OK", "result": []}

    async def close(self) -> None:
        self.closed = True


class MockSyncTransport:
    """In-memory sync transport that returns pre-configured responses."""

    def __init__(self) -> None:
        self.responses: dict[str, dict[str, Any]] = {}
        self.calls: list[tuple[str, str, dict[str, str]]] = []
        self.closed = False

    def set_response(self, url_contains: str, data: dict[str, Any]) -> None:
        self.responses[url_contains] = data

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str],
    ) -> dict[str, Any]:
        self.calls.append((method, url, params))
        for pattern, data in self.responses.items():
            if pattern in url:
                return data
        return {"status": "1", "message": "OK", "result": []}

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def mock_async_transport() -> MockAsyncTransport:
    return MockAsyncTransport()


@pytest.fixture
def mock_sync_transport() -> MockSyncTransport:
    return MockSyncTransport()


# ---------------------------------------------------------------------------
# Provider fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_providers() -> ProviderSet:
    """A ProviderSet with all three providers, Etherscan keyed."""
    return ProviderSet(
        [
            ProviderCredential(type="etherscan", api_key="TEST_KEY", tier=EtherscanTier.FREE),
            ProviderCredential(type="routescan", tier=RoutescanTier.ANONYMOUS),
            ProviderCredential(type="blockscout"),
        ]
    )
