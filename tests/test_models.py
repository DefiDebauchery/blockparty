"""Tests for blockparty.models.responses — Pydantic model validation."""

from __future__ import annotations

from blockparty.models.responses import (
    BeaconWithdrawal,
    EthPrice,
    ExplorerResponse,
    InternalTransaction,
    ObjectResponse,
    ScalarResponse,
)


class TestInternalTransaction:
    def test_parse_etherscan_format(self):
        tx = InternalTransaction.model_validate(
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
                "traceId": "0_1",
            }
        )
        assert tx.block_number == 100
        assert tx.from_address == "0xA"
        assert tx.value == 1000000
        assert tx.is_error is False
        assert tx.trace_id == "0_1"

    def test_hex_coercion(self):
        tx = InternalTransaction.model_validate(
            {
                "blockNumber": "0xc48174",
                "timeStamp": "0x60f9ce56",
                "hash": "0x1",
                "from": "0xA",
                "to": "0xB",
                "value": "0x0",
                "contractAddress": "",
                "input": "",
                "type": "call",
                "gas": "0x5208",
                "gasUsed": "0x5208",
                "isError": "0",
                "errCode": "",
            }
        )
        assert tx.block_number == 12_878_196
        assert tx.gas == 21000


class TestResponseEnvelopes:
    def test_explorer_response_with_list(self):
        resp = ExplorerResponse[InternalTransaction].model_validate(
            {
                "status": "1",
                "message": "OK",
                "result": [
                    {
                        "blockNumber": "100",
                        "timeStamp": "1000",
                        "hash": "0x1",
                        "from": "0xA",
                        "to": "0xB",
                        "value": "0",
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
        )
        assert len(resp.result) == 1

    def test_scalar_response(self):
        assert ScalarResponse.model_validate({"status": "1", "message": "OK", "result": "12345"}).result == "12345"

    def test_object_response(self):
        resp = ObjectResponse[EthPrice].model_validate(
            {
                "status": "1",
                "message": "OK",
                "result": {"ethbtc": "0.05", "ethbtc_timestamp": "1", "ethusd": "3000", "ethusd_timestamp": "1"},
            }
        )
        assert resp.result.ethusd == "3000"

    def test_beacon_withdrawal(self):
        bw = BeaconWithdrawal.model_validate(
            {
                "withdrawalIndex": "13",
                "validatorIndex": "117823",
                "address": "0xABC",
                "amount": "3402931175",
                "blockNumber": "17034877",
                "timestamp": "1681338599",
            }
        )
        assert bw.withdrawal_index == 13
        assert bw.amount == 3402931175
