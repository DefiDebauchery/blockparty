"""Tests for SyncBlockpartyClient with mock transport."""

from __future__ import annotations

import warnings

import pytest

from blockparty.client.sync_client import SyncBlockpartyClient
from blockparty.exceptions import InvalidAddressError, PoolExhaustedError
from blockparty.pool._base import ProviderCredential, ProviderSet


def _ok_response(result=None):
    return {"status": "1", "message": "OK", "result": result or []}


def _error_response(message="NOTOK", result="Error"):
    return {"status": "0", "message": message, "result": result}


class TestSyncClientBasic:
    def test_get_balance(self, mock_registry, mock_sync_transport):
        mock_sync_transport.set_response("etherscan.io", _ok_response("12345"))
        with SyncBlockpartyClient(
            chain_id=1,
            registry=mock_registry,
            transport=mock_sync_transport,
        ) as client:
            result = client.get_balance(address="0xABC")
        assert result.result == "12345"

    def test_limit_maps_to_offset(self, mock_registry, mock_sync_transport):
        mock_sync_transport.set_response("etherscan.io", _ok_response())
        with SyncBlockpartyClient(
            chain_id=1,
            registry=mock_registry,
            transport=mock_sync_transport,
        ) as client:
            client.get_normal_transactions(address="0xABC", limit=25)
        _, _, params = mock_sync_transport.calls[0]
        assert params["offset"] == "25"

    def test_context_manager_doesnt_close_user_transport(self, mock_registry, mock_sync_transport):
        with SyncBlockpartyClient(
            chain_id=1,
            registry=mock_registry,
            transport=mock_sync_transport,
        ):
            pass
        assert not mock_sync_transport.closed


class TestSyncClientFallback:
    def test_fallback_on_error(self, mock_registry, mock_sync_transport):
        mock_sync_transport.set_response("etherscan.io", _error_response("NOTOK", "Max rate limit reached"))
        mock_sync_transport.set_response("routescan.io", _ok_response("fallback"))

        providers = ProviderSet(
            [
                ProviderCredential(type="etherscan", api_key="K"),
                ProviderCredential(type="routescan"),
            ]
        )
        with SyncBlockpartyClient(
            chain_id=1,
            providers=providers,
            registry=mock_registry,
            transport=mock_sync_transport,
        ) as client:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = client.get_balance(address="0xABC")
        assert result.result == "fallback"
        assert len(w) >= 1

    def test_invalid_address_no_fallback(self, mock_registry, mock_sync_transport):
        mock_sync_transport.set_response("etherscan.io", _error_response("NOTOK", "Error! Invalid address format"))
        providers = ProviderSet(
            [
                ProviderCredential(type="etherscan", api_key="K"),
                ProviderCredential(type="routescan"),
            ]
        )
        with SyncBlockpartyClient(
            chain_id=1,
            providers=providers,
            registry=mock_registry,
            transport=mock_sync_transport,
        ) as client:
            with pytest.raises(InvalidAddressError):
                client.get_balance(address="bad")

    def test_all_fail_pool_exhausted(self, mock_registry, mock_sync_transport):
        mock_sync_transport.set_response("etherscan.io", _error_response("NOTOK", "Max rate limit reached"))
        mock_sync_transport.set_response("routescan.io", _error_response("NOTOK", "Max rate limit reached"))
        providers = ProviderSet(
            [
                ProviderCredential(type="etherscan", api_key="K"),
                ProviderCredential(type="routescan"),
            ]
        )
        with SyncBlockpartyClient(
            chain_id=1,
            providers=providers,
            registry=mock_registry,
            transport=mock_sync_transport,
        ) as client:
            with pytest.raises(PoolExhaustedError):
                client.get_balance(address="0xABC")
