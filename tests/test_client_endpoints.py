"""Tests for blockparty.client._endpoints — param mapping and response parsing."""

from __future__ import annotations

import pytest

from blockparty.backends.etherscan import EtherscanBackend
from blockparty.client._endpoints import (
    ENDPOINT_REGISTRY,
    build_call_kwargs,
    parse_endpoint_response,
)
from blockparty.client._params import prepare_list_param


class TestPrepareListParam:
    def test_string_passthrough(self):
        assert prepare_list_param("0xABC", max_items=20, param_name="address") == "0xABC"

    def test_list_joined(self):
        assert prepare_list_param(["a", "b", "c"], max_items=5, param_name="x") == "a,b,c"

    def test_limit_exceeded(self):
        with pytest.raises(ValueError, match="at most 3"):
            prepare_list_param(["a", "b", "c", "d"], max_items=3, param_name="test")


class TestBuildCallKwargs:
    def test_basic_mapping(self):
        ep = ENDPOINT_REGISTRY["get_internal_transactions"]
        result = build_call_kwargs(
            ep,
            {
                "address": "0xABC",
                "start_block": 100,
                "end_block": 200,
                "limit": 50,
                "sort": "asc",
            },
        )
        assert result["module"] == "account"
        assert result["action"] == "txlistinternal"
        assert result["startblock"] == 100
        assert result["endblock"] == 200
        assert result["offset"] == 50  # limit → offset alias

    def test_none_values_dropped(self):
        ep = ENDPOINT_REGISTRY["get_erc20_token_transfers"]
        result = build_call_kwargs(
            ep,
            {
                "address": "0x",
                "contract_address": None,
                "end_block": None,
            },
        )
        assert "contractaddress" not in result
        assert "endblock" not in result

    def test_list_param_comma_joined(self):
        ep = ENDPOINT_REGISTRY["get_balance"]
        result = build_call_kwargs(ep, {"address": ["0xA", "0xB", "0xC"], "tag": "latest"})
        assert result["address"] == "0xA,0xB,0xC"

    def test_list_param_limit_enforced(self):
        ep = ENDPOINT_REGISTRY["get_contract_creation"]
        with pytest.raises(ValueError, match="at most 5"):
            build_call_kwargs(
                ep,
                {
                    "contract_addresses": ["0x1", "0x2", "0x3", "0x4", "0x5", "0x6"],
                },
            )

    def test_contract_address_mapping(self):
        ep = ENDPOINT_REGISTRY["get_token_balance"]
        result = build_call_kwargs(
            ep,
            {
                "contract_address": "0xTOKEN",
                "address": "0xUSER",
                "tag": "latest",
            },
        )
        assert result["contractaddress"] == "0xTOKEN"
        assert "contract_address" not in result

    def test_dynamic_action_override(self):
        ep = ENDPOINT_REGISTRY["get_daily_stats"]
        result = build_call_kwargs(
            ep,
            {
                "action": "dailyavgblocksize",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "sort": "asc",
            },
        )
        assert result["action"] == "dailyavgblocksize"
        assert result["startdate"] == "2024-01-01"

    def test_no_params_endpoint(self):
        result = build_call_kwargs(ENDPOINT_REGISTRY["get_gas_oracle"], {})
        assert result == {"module": "gastracker", "action": "gasoracle"}


class TestEndpointRegistry:
    def test_has_expected_endpoints(self):
        expected = [
            "get_balance",
            "get_normal_transactions",
            "get_internal_transactions",
            "get_erc20_token_transfers",
            "get_contract_abi",
            "get_contract_source_code",
            "get_logs",
            "get_eth_price",
            "get_gas_oracle",
            "get_token_info",
            "get_daily_stats",
            "get_chainlist",
        ]
        for name in expected:
            assert name in ENDPOINT_REGISTRY, f"Missing: {name}"

    def test_all_have_module_and_action(self):
        for name, ep in ENDPOINT_REGISTRY.items():
            assert ep.module, f"{name} missing module"
            assert ep.action, f"{name} missing action"


class TestParseEndpointResponse:
    def test_scalar_response(self):
        data = {"status": "1", "message": "OK", "result": "123456789"}
        result = parse_endpoint_response(ENDPOINT_REGISTRY["get_balance"], data, EtherscanBackend())
        assert result.result == "123456789"

    def test_list_response(self):
        data = {
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "blockNumber": "100",
                    "blockHash": "0x",
                    "timeStamp": "1000",
                    "hash": "0xabc",
                    "nonce": "1",
                    "transactionIndex": "0",
                    "from": "0xA",
                    "to": "0xB",
                    "value": "0",
                    "gas": "21000",
                    "gasPrice": "1000",
                    "input": "0x",
                    "contractAddress": "",
                    "cumulativeGasUsed": "21000",
                    "gasUsed": "21000",
                    "confirmations": "10",
                    "isError": "0",
                }
            ],
        }
        result = parse_endpoint_response(
            ENDPOINT_REGISTRY["get_normal_transactions"],
            data,
            EtherscanBackend(),
        )
        assert len(result.result) == 1
        assert result.result[0].hash == "0xabc"

    def test_object_response(self):
        data = {
            "status": "1",
            "message": "OK",
            "result": {
                "ethbtc": "0.05",
                "ethbtc_timestamp": "1000",
                "ethusd": "3000.0",
                "ethusd_timestamp": "1000",
            },
        }
        result = parse_endpoint_response(
            ENDPOINT_REGISTRY["get_eth_price"],
            data,
            EtherscanBackend(),
        )
        assert result.result.ethusd == "3000.0"

    def test_error_raises(self):
        data = {"status": "0", "message": "NOTOK", "result": "Invalid address"}
        with pytest.raises(Exception):
            parse_endpoint_response(ENDPOINT_REGISTRY["get_balance"], data, EtherscanBackend())
