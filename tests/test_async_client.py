"""Tests for AsyncBlockpartyClient with mock transport."""

from __future__ import annotations

import warnings

import pytest

from blockparty.client._transport import TransportConnectionError
from blockparty.client.async_client import AsyncBlockpartyClient
from blockparty.exceptions import (
    InvalidAddressError,
    PoolExhaustedError,
)
from blockparty.pool._base import ProviderCredential, ProviderSet
from blockparty.ratelimit.tiers import EtherscanTier, RoutescanTier
from blockparty.warnings import AuthFallbackWarning, FallbackWarning

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok_response(result=None):
    """Build a standard success response."""
    return {"status": "1", "message": "OK", "result": result or []}


def _error_response(message="NOTOK", result="Error"):
    return {"status": "0", "message": message, "result": result}


def _internal_tx_response():
    """A valid internal transactions response."""
    return {
        "status": "1",
        "message": "OK",
        "result": [
            {
                "blockNumber": "100",
                "timeStamp": "1000",
                "hash": "0xabc",
                "from": "0xA",
                "to": "0xB",
                "value": "1000000",
                "contractAddress": "",
                "input": "",
                "type": "call",
                "gas": "21000",
                "gasUsed": "21000",
                "isError": "0",
                "errCode": "",
            }
        ],
    }


# ---------------------------------------------------------------------------
# Basic lifecycle
# ---------------------------------------------------------------------------


class TestAsyncClientLifecycle:
    @pytest.mark.asyncio
    async def test_context_manager(self, mock_registry, mock_async_transport):
        mock_async_transport.set_response("etherscan.io", _ok_response("12345"))
        async with AsyncBlockpartyClient(
            chain_id=1,
            registry=mock_registry,
            transport=mock_async_transport,
        ) as client:
            assert client.chain_id == 1
        # Transport NOT closed (we don't own it)
        assert not mock_async_transport.closed

    @pytest.mark.asyncio
    async def test_explorer_type_property(self, mock_registry, mock_async_transport):
        client = AsyncBlockpartyClient(
            chain_id=1,
            explorer_type="routescan",
            registry=mock_registry,
            transport=mock_async_transport,
        )
        assert client.explorer_type == "routescan"

    @pytest.mark.asyncio
    async def test_chain_not_in_registry(self, mock_registry, mock_async_transport):
        with pytest.raises(Exception):  # ChainNotFoundError
            AsyncBlockpartyClient(
                chain_id=999999,
                registry=mock_registry,
                transport=mock_async_transport,
            )


# ---------------------------------------------------------------------------
# Basic API calls
# ---------------------------------------------------------------------------


class TestAsyncClientAPICalls:
    @pytest.mark.asyncio
    async def test_get_balance(self, mock_registry, mock_async_transport):
        mock_async_transport.set_response("etherscan.io", _ok_response("172774397764"))
        async with AsyncBlockpartyClient(
            chain_id=1,
            registry=mock_registry,
            transport=mock_async_transport,
        ) as client:
            result = await client.get_balance(address="0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae")

        assert result.result == "172774397764"
        # Verify the API was called with correct params
        method, url, params = mock_async_transport.calls[0]
        assert method == "GET"
        assert params["module"] == "account"
        assert params["action"] == "balance"
        assert params["address"] == "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae"

    @pytest.mark.asyncio
    async def test_get_internal_transactions(self, mock_registry, mock_async_transport):
        mock_async_transport.set_response("etherscan.io", _internal_tx_response())
        async with AsyncBlockpartyClient(
            chain_id=1,
            registry=mock_registry,
            transport=mock_async_transport,
        ) as client:
            result = await client.get_internal_transactions(
                address="0xABC",
                start_block=100,
                limit=50,
                sort="asc",
            )

        assert len(result.result) == 1
        assert result.result[0].hash == "0xabc"
        # Verify limit → offset mapping
        _, _, params = mock_async_transport.calls[0]
        assert params["offset"] == "50"
        assert params["startblock"] == "100"
        assert "limit" not in params

    @pytest.mark.asyncio
    async def test_get_eth_price(self, mock_registry, mock_async_transport):
        mock_async_transport.set_response(
            "etherscan.io",
            _ok_response(
                {
                    "ethbtc": "0.05",
                    "ethbtc_timestamp": "1000",
                    "ethusd": "3000",
                    "ethusd_timestamp": "1000",
                }
            ),
        )
        async with AsyncBlockpartyClient(
            chain_id=1,
            registry=mock_registry,
            transport=mock_async_transport,
        ) as client:
            result = await client.get_eth_price()

        assert result.result.ethusd == "3000"

    @pytest.mark.asyncio
    async def test_multi_address_balance(self, mock_registry, mock_async_transport):
        mock_async_transport.set_response("etherscan.io", _ok_response("100,200,300"))
        async with AsyncBlockpartyClient(
            chain_id=1,
            registry=mock_registry,
            transport=mock_async_transport,
        ) as client:
            await client.get_balance(address=["0xA", "0xB", "0xC"])

        _, _, params = mock_async_transport.calls[0]
        assert params["address"] == "0xA,0xB,0xC"


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------


class TestAsyncClientCaching:
    @pytest.mark.asyncio
    async def test_second_call_is_cached(self, mock_registry, mock_async_transport):
        mock_async_transport.set_response("etherscan.io", _ok_response("12345"))
        async with AsyncBlockpartyClient(
            chain_id=1,
            registry=mock_registry,
            transport=mock_async_transport,
            cache_ttl=60,
        ) as client:
            r1 = await client.get_balance(address="0xABC")
            r2 = await client.get_balance(address="0xABC")

        assert len(mock_async_transport.calls) == 1  # Only one HTTP call
        assert r1.result == r2.result

    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_cache(self, mock_registry, mock_async_transport):
        mock_async_transport.set_response("etherscan.io", _ok_response("12345"))
        async with AsyncBlockpartyClient(
            chain_id=1,
            registry=mock_registry,
            transport=mock_async_transport,
            cache_ttl=60,
        ) as client:
            await client.get_balance(address="0xABC")
            await client.get_balance(address="0xABC", force_refresh=True)

        assert len(mock_async_transport.calls) == 2


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------


class TestAsyncClientFallback:
    @pytest.mark.asyncio
    async def test_fallback_on_rate_limit(self, mock_registry, mock_async_transport):
        """If etherscan returns rate limit, fallback to routescan."""
        mock_async_transport.set_response("etherscan.io", _error_response("NOTOK", "Max rate limit reached"))
        mock_async_transport.set_response("routescan.io", _ok_response("999"))

        providers = ProviderSet(
            [
                ProviderCredential(type="etherscan", api_key="K", tier=EtherscanTier.FREE),
                ProviderCredential(type="routescan", tier=RoutescanTier.ANONYMOUS),
            ]
        )
        async with AsyncBlockpartyClient(
            chain_id=1,
            providers=providers,
            registry=mock_registry,
            transport=mock_async_transport,
        ) as client:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = await client.get_balance(address="0xABC")

        assert result.result == "999"
        assert len(w) == 1
        assert issubclass(w[0].category, FallbackWarning)

    @pytest.mark.asyncio
    async def test_fallback_on_auth_error(self, mock_registry, mock_async_transport):
        mock_async_transport.set_response("etherscan.io", _error_response("NOTOK", "Invalid API key"))
        mock_async_transport.set_response("routescan.io", _ok_response("42"))

        providers = ProviderSet(
            [
                ProviderCredential(type="etherscan", api_key="BAD_KEY"),
                ProviderCredential(type="routescan"),
            ]
        )
        async with AsyncBlockpartyClient(
            chain_id=1,
            providers=providers,
            registry=mock_registry,
            transport=mock_async_transport,
        ) as client:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = await client.get_balance(address="0xABC")

        assert result.result == "42"
        assert any(issubclass(x.category, AuthFallbackWarning) for x in w)

    @pytest.mark.asyncio
    async def test_non_fallback_error_raises_immediately(self, mock_registry, mock_async_transport):
        mock_async_transport.set_response("etherscan.io", _error_response("NOTOK", "Error! Invalid address format"))

        providers = ProviderSet(
            [
                ProviderCredential(type="etherscan", api_key="K"),
                ProviderCredential(type="routescan"),
            ]
        )
        async with AsyncBlockpartyClient(
            chain_id=1,
            providers=providers,
            registry=mock_registry,
            transport=mock_async_transport,
        ) as client:
            with pytest.raises(InvalidAddressError):
                await client.get_balance(address="bad")

        # Routescan should NOT have been called
        assert all("routescan" not in url for _, url, _ in mock_async_transport.calls)

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_pool_exhausted(self, mock_registry, mock_async_transport):
        mock_async_transport.set_response("etherscan.io", _error_response("NOTOK", "Max rate limit reached"))
        mock_async_transport.set_response("routescan.io", _error_response("NOTOK", "Max rate limit reached"))
        mock_async_transport.set_response("blockscout.com", _error_response("NOTOK", "Max rate limit reached"))

        providers = ProviderSet(
            [
                ProviderCredential(type="etherscan", api_key="K"),
                ProviderCredential(type="routescan"),
                ProviderCredential(type="blockscout"),
            ]
        )
        async with AsyncBlockpartyClient(
            chain_id=1,
            providers=providers,
            registry=mock_registry,
            transport=mock_async_transport,
        ) as client:
            with pytest.raises(PoolExhaustedError) as exc_info:
                await client.get_balance(address="0xABC")

        assert len(exc_info.value.provider_errors) == 3

    @pytest.mark.asyncio
    async def test_fallback_on_transport_error(self, mock_registry):
        """Transport-level errors (connection failures) trigger fallback."""

        class FailThenSucceedTransport:
            def __init__(self):
                self.call_count = 0

            async def request(self, method, url, *, params):
                self.call_count += 1
                if "etherscan.io" in url:
                    raise TransportConnectionError("connection refused")
                return _ok_response("fallback_worked")

            async def close(self):
                pass

        transport = FailThenSucceedTransport()
        providers = ProviderSet(
            [
                ProviderCredential(type="etherscan", api_key="K"),
                ProviderCredential(type="routescan"),
            ]
        )
        async with AsyncBlockpartyClient(
            chain_id=1,
            providers=providers,
            registry=mock_registry,
            transport=transport,
        ) as client:
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                result = await client.get_balance(address="0xABC")

        assert result.result == "fallback_worked"
        assert transport.call_count == 2


# ---------------------------------------------------------------------------
# Provider stamping
# ---------------------------------------------------------------------------


class TestAsyncClientProviderStamp:
    @pytest.mark.asyncio
    async def test_response_has_provider(self, mock_registry, mock_async_transport):
        mock_async_transport.set_response("etherscan.io", _ok_response("12345"))
        async with AsyncBlockpartyClient(
            chain_id=1,
            explorer_type="etherscan",
            api_key="K",
            registry=mock_registry,
            transport=mock_async_transport,
        ) as client:
            result = await client.get_balance(address="0xABC")
        assert result.provider == "etherscan"

    @pytest.mark.asyncio
    async def test_fallback_stamps_actual_provider(self, mock_registry, mock_async_transport):
        """After fallback, provider should reflect who actually answered."""
        mock_async_transport.set_response("etherscan.io", _error_response("NOTOK", "Max rate limit reached"))
        mock_async_transport.set_response("routescan.io", _ok_response("999"))

        providers = ProviderSet(
            [
                ProviderCredential(type="etherscan", api_key="K"),
                ProviderCredential(type="routescan"),
            ]
        )
        async with AsyncBlockpartyClient(
            chain_id=1,
            providers=providers,
            registry=mock_registry,
            transport=mock_async_transport,
        ) as client:
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                result = await client.get_balance(address="0xABC")

        assert result.provider == "routescan"

    @pytest.mark.asyncio
    async def test_cached_response_has_provider(self, mock_registry, mock_async_transport):
        mock_async_transport.set_response("etherscan.io", _ok_response("12345"))
        async with AsyncBlockpartyClient(
            chain_id=1,
            registry=mock_registry,
            transport=mock_async_transport,
            cache_ttl=60,
        ) as client:
            first = await client.get_balance(address="0xABC")
            second = await client.get_balance(address="0xABC")  # cache hit

        assert first.provider == "etherscan"
        assert second.provider == "etherscan"
        assert len(mock_async_transport.calls) == 1  # only one HTTP call

    @pytest.mark.asyncio
    async def test_urls_for_matches_provider(self, mock_registry, mock_async_transport):
        """urls_for(resp.provider) returns URLs from the actual responding explorer."""
        mock_async_transport.set_response("etherscan.io", _error_response("NOTOK", "Max rate limit reached"))
        mock_async_transport.set_response("blockscout.com", _ok_response("42"))

        providers = ProviderSet(
            [
                ProviderCredential(type="etherscan", api_key="K"),
                ProviderCredential(type="blockscout"),
            ]
        )
        async with AsyncBlockpartyClient(
            chain_id=1,
            providers=providers,
            registry=mock_registry,
            transport=mock_async_transport,
        ) as client:
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                result = await client.get_balance(address="0xABC")

            preferred = client.urls
            actual = client.urls_for(result.provider)

        assert result.provider == "blockscout"
        assert preferred.address("0x1") != actual.address("0x1")
        assert "blockscout" in actual.address("0x1").lower()

    @pytest.mark.asyncio
    async def test_urls_for_none_returns_preferred(self, mock_registry, mock_async_transport):
        mock_async_transport.set_response("etherscan.io", _ok_response("1"))
        async with AsyncBlockpartyClient(
            chain_id=1,
            registry=mock_registry,
            transport=mock_async_transport,
        ) as client:
            preferred = client.urls
            from_none = client.urls_for(None)

        assert preferred.address("0x1") == from_none.address("0x1")
