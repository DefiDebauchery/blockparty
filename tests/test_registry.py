"""Tests for blockparty.registry.chain_registry."""

from __future__ import annotations

import pytest

from blockparty.exceptions import ChainNotFoundError, ExplorerNotFoundError
from blockparty.registry.chain_registry import ChainRegistry


class TestChainRegistryBundled:
    @pytest.fixture
    def registry(self):
        return ChainRegistry.load()

    def test_load_has_entries(self, registry):
        assert len(registry) > 0

    def test_get_ethereum(self, registry):
        entry = registry.get(1)
        assert entry.name == "Ethereum Mainnet"
        assert not entry.is_testnet

    def test_get_missing_raises(self, registry):
        with pytest.raises(ChainNotFoundError):
            registry.get(2147483647)

    def test_contains(self, registry):
        assert 1 in registry
        assert 2147483647 not in registry

    def test_search(self, registry):
        results = registry.search("ethereum")
        assert any(e.chain_id == 1 for e in results)

    def test_list_chains_sorted(self, registry):
        chains = registry.list_chains()
        ids = [c.chain_id for c in chains]
        assert ids == sorted(ids)

    def test_get_explorer_auto_resolves(self, registry):
        info = registry.get_explorer(1)
        assert info.type in ("etherscan", "routescan", "blockscout")

    def test_get_explorer_explicit_type(self, registry):
        assert registry.get_explorer(1, "etherscan").type == "etherscan"

    def test_get_explorer_missing_type_raises(self, registry):
        with pytest.raises(ExplorerNotFoundError):
            registry.get_explorer(1, "nonexistent_type")  # type: ignore


class TestChainRegistryMock:
    def test_blockscout_only_chain(self, mock_registry):
        entry = mock_registry.get(999)
        assert len(entry.explorers) == 1
        assert entry.explorers[0].type == "blockscout"
