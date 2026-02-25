"""Tests for blockparty.urls.builder."""

from __future__ import annotations

import pytest

from blockparty.urls.builder import ExplorerURLs


class TestEtherscanURLs:
    @pytest.fixture
    def urls(self):
        return ExplorerURLs(explorer_type="etherscan", frontend_url="https://etherscan.io/")

    @pytest.mark.parametrize(
        "method, arg, expected_suffix",
        [
            ("address", "0xABC", "/address/0xABC"),
            ("tx", "0x123", "/tx/0x123"),
            ("token", "0xTOK", "/token/0xTOK"),
            ("block", 12345, "/block/12345"),
        ],
    )
    def test_url_paths(self, urls, method, arg, expected_suffix):
        result = getattr(urls, method)(arg)
        assert result == f"https://etherscan.io{expected_suffix}"

    def test_blocks_listing(self, urls):
        assert urls.blocks() == "https://etherscan.io/blocks"


class TestBlockscoutURLs:
    def test_address(self):
        urls = ExplorerURLs(explorer_type="blockscout", frontend_url="https://base.blockscout.com/")
        assert urls.address("0xABC") == "https://base.blockscout.com/address/0xABC"


class TestRoutescanURLs:
    def test_vanity_address(self):
        urls = ExplorerURLs(
            explorer_type="routescan",
            frontend_url="https://routescan.io",
            frontend_url_vanity="https://basescan.routescan.io",
            chain_id=8453,
        )
        assert urls.address("0xA") == "https://basescan.routescan.io/address/0xA"

    def test_vanity_block_includes_chainid(self):
        urls = ExplorerURLs(
            explorer_type="routescan",
            frontend_url="https://routescan.io",
            frontend_url_vanity="https://basescan.routescan.io",
            chain_id=8453,
        )
        url = urls.block(100)
        assert "basescan.routescan.io/block/100" in url
        assert "chainid=8453" in url

    def test_generic_fallback_includes_chainid(self):
        urls = ExplorerURLs(
            explorer_type="routescan",
            frontend_url="https://routescan.io",
            chain_id=8453,
            is_testnet=False,
        )
        assert "routescan.io/address/0xA?chainid=8453" in urls.address("0xA")

    def test_testnet_uses_testnet_host(self):
        urls = ExplorerURLs(
            explorer_type="routescan",
            frontend_url="https://routescan.io",
            chain_id=11155111,
            is_testnet=True,
        )
        assert "testnet.routescan.io" in urls.address("0xA")
