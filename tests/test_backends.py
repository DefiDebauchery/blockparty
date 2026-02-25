"""Tests for blockparty.backends — error classification and provider behavior."""

from __future__ import annotations

from blockparty.backends._errors import classify_error
from blockparty.backends.blockscout import BlockscoutBackend
from blockparty.backends.etherscan import EtherscanBackend
from blockparty.exceptions import (
    ChainNotSupportedError,
    ExplorerAPIError,
    InvalidAddressError,
    InvalidAPIKeyError,
    PremiumEndpointError,
    RateLimitError,
)


class TestClassifyError:
    def test_invalid_api_key(self):
        assert isinstance(classify_error("NOTOK", "Missing or invalid API key"), InvalidAPIKeyError)

    def test_rate_limit(self):
        assert isinstance(classify_error("NOTOK", "Max rate limit reached"), RateLimitError)

    def test_invalid_address(self):
        assert isinstance(classify_error("NOTOK", "Error! Invalid address format"), InvalidAddressError)

    def test_premium_endpoint(self):
        assert isinstance(
            classify_error("NOTOK", "trying to access an API Pro endpoint"),
            PremiumEndpointError,
        )

    def test_chain_not_supported(self):
        assert isinstance(
            classify_error("NOTOK", "not supported for this chain"),
            ChainNotSupportedError,
        )

    def test_unknown_error_falls_back_to_base(self):
        err = classify_error("NOTOK", "Something unexpected")
        assert type(err) is ExplorerAPIError

    def test_searches_both_message_and_result(self):
        """Pattern matching should search the combined message + result text."""
        assert isinstance(classify_error("NOTOK", "invalid api key in result"), InvalidAPIKeyError)


class TestEtherscanBackend:
    def test_build_request_params(self):
        params = EtherscanBackend().build_request_params(
            module="account",
            action="txlist",
            api_key="KEY",
            address="0xABC",
        )
        assert params == {"module": "account", "action": "txlist", "apikey": "KEY", "address": "0xABC"}

    def test_build_request_params_drops_none(self):
        params = EtherscanBackend().build_request_params(
            module="account",
            action="balance",
            api_key=None,
            tag=None,
        )
        assert "apikey" not in params
        assert "tag" not in params

    def test_parse_error_success_returns_none(self):
        assert EtherscanBackend().parse_error({"status": "1", "message": "OK", "result": []}) is None

    def test_parse_error_failure_returns_typed_error(self):
        err = EtherscanBackend().parse_error({"status": "0", "message": "NOTOK", "result": "Invalid address"})
        assert isinstance(err, InvalidAddressError)

    def test_normalize_is_passthrough(self):
        raw = {"hash": "0x123", "type": "call"}
        assert EtherscanBackend().normalize_internal_tx(raw) is raw


class TestBlockscoutBackend:
    def test_normalize_remaps_fields(self):
        raw = {"transactionHash": "0x123", "callType": "delegatecall"}
        normalized = BlockscoutBackend().normalize_internal_tx(raw)
        assert normalized["hash"] == "0x123"
        assert normalized["type"] == "delegatecall"
        assert "transactionHash" not in normalized

    def test_normalize_preserves_existing_hash(self):
        raw = {"hash": "0xABC", "transactionHash": "0x123"}
        assert BlockscoutBackend().normalize_internal_tx(raw)["hash"] == "0xABC"

    def test_parse_error_ok_returns_none(self):
        assert BlockscoutBackend().parse_error({"message": "OK", "result": []}) is None

    def test_parse_error_list_result_returns_none(self):
        assert BlockscoutBackend().parse_error({"message": "", "result": [{"hash": "0x"}]}) is None

    def test_parse_error_detects_error_message(self):
        err = BlockscoutBackend().parse_error({"message": "Invalid address", "result": ""})
        assert isinstance(err, InvalidAddressError)
