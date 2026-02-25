"""Endpoint descriptors — define each API endpoint once.

Each :class:`Endpoint` captures the module, action, parameter specifications,
response shape, and optional Pydantic model.  The ``ENDPOINT_REGISTRY`` dict
maps public method names to their endpoint descriptors.

The :func:`build_call_kwargs` function translates Python keyword arguments
(using developer-friendly names like ``start_block``, ``limit``) into API
query parameter names (``startblock``, ``offset``).

Response parsing via :func:`parse_endpoint_response` dispatches to the
correct parse helper based on the endpoint's :class:`ResponseShape`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from pydantic import BaseModel

from blockparty.backends._base import ExplorerBackend
from blockparty.client._base import (
    parse_internal_tx_response,
    parse_list_response,
    parse_object_response,
    parse_scalar_response,
)
from blockparty.client._params import prepare_list_param
from blockparty.models.responses import (
    AddressNFTInventory,
    AddressTokenBalance,
    BeaconWithdrawal,
    BlockReward,
    ChainListEntry,
    ContractCreation,
    ContractSourceCode,
    DailyStatistic,
    DepositTransaction,
    ERC20TokenTransfer,
    ERC721TokenTransfer,
    ERC1155TokenTransfer,
    EthPrice,
    EthSupply2,
    EventLog,
    FundedBy,
    GasOracle,
    MinedBlock,
    NodeCount,
    NormalTransaction,
    PlasmaDeposit,
    TokenHolderEntry,
    TokenInfo,
    TopTokenHolder,
    TransactionReceiptStatus,
    TransactionStatus,
)

# ---------------------------------------------------------------------------
# Response shape enum
# ---------------------------------------------------------------------------


class ResponseShape(Enum):
    """How to parse the API response."""

    LIST = auto()
    SCALAR = auto()
    OBJECT = auto()
    INTERNAL_TX = auto()


# ---------------------------------------------------------------------------
# Parameter specification
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ParamSpec:
    """Describes one query-string parameter for an endpoint.

    Attributes:
        api_name: Name used in the query string (e.g. ``"contractaddress"``).
        python_name: Name used as the Python keyword argument.  Defaults to
            *api_name* when empty.  Allows developer-friendly aliases like
            ``limit`` for the API's ``offset`` param.
        max_items: If set, the parameter accepts ``str | list[str]`` with a
            max-items limit and is automatically comma-joined.
    """

    api_name: str
    python_name: str = ""
    max_items: int | None = None


# ---------------------------------------------------------------------------
# Endpoint descriptor
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Endpoint:
    """Declarative description of a single Etherscan API endpoint.

    Attributes:
        module: The API module (e.g. ``"account"``, ``"contract"``).
        action: The API action (e.g. ``"txlist"``).  ``"__dynamic__"``
            indicates the action is passed at call time (e.g. daily stats).
        shape: How the response ``result`` should be parsed.
        model: The Pydantic model for list/object responses.
        params: Ordered list of query parameters accepted by this endpoint.
    """

    module: str
    action: str
    shape: ResponseShape
    model: type[BaseModel] | None = None
    params: list[ParamSpec] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Build call kwargs
# ---------------------------------------------------------------------------


def build_call_kwargs(ep: Endpoint, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Translate Python kwargs into API query parameter names.

    Maps developer-friendly names (``start_block``, ``limit``) to API names
    (``startblock``, ``offset``).  Handles list-param validation and
    comma-joining.  Drops ``None`` values.

    The ``action`` kwarg overrides the endpoint's static action when
    present (used by daily stats with dynamic action).

    Returns:
        A flat dict of ``{api_param_name: stringified_value}`` ready for
        the HTTP request.
    """
    action = kwargs.pop("action", ep.action)
    params: dict[str, Any] = {"module": ep.module, "action": action}

    # Build reverse map: python_name → ParamSpec.
    py_to_spec: dict[str, ParamSpec] = {}
    for ps in ep.params:
        py_name = ps.python_name or ps.api_name
        py_to_spec[py_name] = ps

    for py_name, value in kwargs.items():
        if value is None:
            continue

        spec = py_to_spec.get(py_name)
        api_name = spec.api_name if spec else py_name

        # Handle list params with comma joining.
        if spec and spec.max_items is not None:
            value = prepare_list_param(
                value,
                max_items=spec.max_items,
                param_name=py_name,
            )

        params[api_name] = value

    return params


# ---------------------------------------------------------------------------
# Parse dispatch
# ---------------------------------------------------------------------------


def parse_endpoint_response(
    ep: Endpoint,
    data: dict[str, Any],
    backend: ExplorerBackend,
) -> Any:
    """Dispatch to the correct parse helper based on the endpoint's shape."""
    match ep.shape:
        case ResponseShape.LIST:
            if ep.model is None:
                return parse_list_response(data, backend, dict)  # type: ignore[arg-type]
            return parse_list_response(data, backend, ep.model)
        case ResponseShape.SCALAR:
            return parse_scalar_response(data, backend)
        case ResponseShape.OBJECT:
            assert ep.model is not None
            return parse_object_response(data, backend, ep.model)
        case ResponseShape.INTERNAL_TX:
            return parse_internal_tx_response(data, backend)


# ---------------------------------------------------------------------------
# Reusable parameter groups
# ---------------------------------------------------------------------------

_PAGINATION = [ParamSpec("page"), ParamSpec("offset", "limit")]
_SORT = ParamSpec("sort")
_BLOCK_RANGE = [
    ParamSpec("startblock", "start_block"),
    ParamSpec("endblock", "end_block"),
]
_TX_LIST_COMMON = [*_BLOCK_RANGE, *_PAGINATION, _SORT]


# ---------------------------------------------------------------------------
# Endpoint registry — every public method name → Endpoint
# ---------------------------------------------------------------------------

ENDPOINT_REGISTRY: dict[str, Endpoint] = {
    # -- Account -----------------------------------------------------------
    "get_normal_transactions": Endpoint(
        module="account",
        action="txlist",
        shape=ResponseShape.LIST,
        model=NormalTransaction,
        params=[ParamSpec("address"), *_TX_LIST_COMMON],
    ),
    "get_internal_transactions": Endpoint(
        module="account",
        action="txlistinternal",
        shape=ResponseShape.INTERNAL_TX,
        params=[ParamSpec("address"), *_TX_LIST_COMMON],
    ),
    "get_internal_transactions_by_hash": Endpoint(
        module="account",
        action="txlistinternal",
        shape=ResponseShape.INTERNAL_TX,
        params=[ParamSpec("txhash")],
    ),
    "get_internal_transactions_by_block_range": Endpoint(
        module="account",
        action="txlistinternal",
        shape=ResponseShape.INTERNAL_TX,
        params=[*_BLOCK_RANGE, *_PAGINATION, _SORT],
    ),
    "get_erc20_token_transfers": Endpoint(
        module="account",
        action="tokentx",
        shape=ResponseShape.LIST,
        model=ERC20TokenTransfer,
        params=[
            ParamSpec("contractaddress", "contract_address"),
            ParamSpec("address"),
            *_TX_LIST_COMMON,
        ],
    ),
    "get_erc721_token_transfers": Endpoint(
        module="account",
        action="tokennfttx",
        shape=ResponseShape.LIST,
        model=ERC721TokenTransfer,
        params=[
            ParamSpec("contractaddress", "contract_address"),
            ParamSpec("address"),
            *_TX_LIST_COMMON,
        ],
    ),
    "get_erc1155_token_transfers": Endpoint(
        module="account",
        action="token1155tx",
        shape=ResponseShape.LIST,
        model=ERC1155TokenTransfer,
        params=[
            ParamSpec("contractaddress", "contract_address"),
            ParamSpec("address"),
            *_TX_LIST_COMMON,
        ],
    ),
    "get_balance": Endpoint(
        module="account",
        action="balance",
        shape=ResponseShape.SCALAR,
        params=[
            ParamSpec("address", max_items=20),
            ParamSpec("tag"),
        ],
    ),
    "get_historical_balance": Endpoint(
        module="account",
        action="balancehistory",
        shape=ResponseShape.SCALAR,
        params=[ParamSpec("address"), ParamSpec("blockno", "block_no")],
    ),
    "get_address_token_balance": Endpoint(
        module="account",
        action="addresstokenbalance",
        shape=ResponseShape.LIST,
        model=AddressTokenBalance,
        params=[ParamSpec("address"), *_PAGINATION],
    ),
    "get_address_nft_inventory": Endpoint(
        module="account",
        action="addresstokennftinventory",
        shape=ResponseShape.LIST,
        model=AddressNFTInventory,
        params=[ParamSpec("address"), ParamSpec("contractaddress", "contract_address"), *_PAGINATION],
    ),
    "get_mined_blocks": Endpoint(
        module="account",
        action="getminedblocks",
        shape=ResponseShape.LIST,
        model=MinedBlock,
        params=[ParamSpec("address"), ParamSpec("blocktype", "block_type"), *_PAGINATION],
    ),
    "get_beacon_withdrawals": Endpoint(
        module="account",
        action="txsBeaconWithdrawal",
        shape=ResponseShape.LIST,
        model=BeaconWithdrawal,
        params=[ParamSpec("address"), *_TX_LIST_COMMON],
    ),
    "get_funded_by": Endpoint(
        module="account",
        action="fundedby",
        shape=ResponseShape.OBJECT,
        model=FundedBy,
        params=[ParamSpec("address")],
    ),
    "get_deposit_transactions": Endpoint(
        module="account",
        action="getdeposittxs",
        shape=ResponseShape.LIST,
        model=DepositTransaction,
        params=[ParamSpec("address"), *_PAGINATION, _SORT],
    ),
    "get_withdrawal_transactions": Endpoint(
        module="account",
        action="getwithdrawaltxs",
        shape=ResponseShape.LIST,
        model=None,
        params=[ParamSpec("address"), *_PAGINATION, _SORT],
    ),
    "get_plasma_deposits": Endpoint(
        module="account",
        action="txnbridge",
        shape=ResponseShape.LIST,
        model=PlasmaDeposit,
        params=[ParamSpec("address"), *_PAGINATION],
    ),
    # -- Contract ----------------------------------------------------------
    "get_contract_abi": Endpoint(
        module="contract",
        action="getabi",
        shape=ResponseShape.SCALAR,
        params=[ParamSpec("address")],
    ),
    "get_contract_source_code": Endpoint(
        module="contract",
        action="getsourcecode",
        shape=ResponseShape.LIST,
        model=ContractSourceCode,
        params=[ParamSpec("address")],
    ),
    "get_contract_creation": Endpoint(
        module="contract",
        action="getcontractcreation",
        shape=ResponseShape.LIST,
        model=ContractCreation,
        params=[ParamSpec("contractaddresses", "contract_addresses", max_items=5)],
    ),
    # -- Transaction -------------------------------------------------------
    "get_transaction_status": Endpoint(
        module="transaction",
        action="getstatus",
        shape=ResponseShape.OBJECT,
        model=TransactionStatus,
        params=[ParamSpec("txhash")],
    ),
    "get_transaction_receipt_status": Endpoint(
        module="transaction",
        action="gettxreceiptstatus",
        shape=ResponseShape.OBJECT,
        model=TransactionReceiptStatus,
        params=[ParamSpec("txhash")],
    ),
    # -- Block -------------------------------------------------------------
    "get_block_reward": Endpoint(
        module="block",
        action="getblockreward",
        shape=ResponseShape.OBJECT,
        model=BlockReward,
        params=[ParamSpec("blockno", "block_no")],
    ),
    "get_block_countdown": Endpoint(
        module="block",
        action="getblockcountdown",
        shape=ResponseShape.SCALAR,
        params=[ParamSpec("blockno", "block_no")],
    ),
    "get_block_no_by_time": Endpoint(
        module="block",
        action="getblocknobytime",
        shape=ResponseShape.SCALAR,
        params=[ParamSpec("timestamp"), ParamSpec("closest")],
    ),
    # -- Logs --------------------------------------------------------------
    "get_logs": Endpoint(
        module="logs",
        action="getLogs",
        shape=ResponseShape.LIST,
        model=EventLog,
        params=[
            ParamSpec("address"),
            ParamSpec("fromBlock", "from_block"),
            ParamSpec("toBlock", "to_block"),
            ParamSpec("topic0"),
            ParamSpec("topic1"),
            ParamSpec("topic2"),
            ParamSpec("topic3"),
            ParamSpec("topic0_1_opr"),
            ParamSpec("topic0_2_opr"),
            ParamSpec("topic0_3_opr"),
            ParamSpec("topic1_2_opr"),
            ParamSpec("topic1_3_opr"),
            ParamSpec("topic2_3_opr"),
            *_PAGINATION,
        ],
    ),
    # -- Token -------------------------------------------------------------
    "get_token_balance": Endpoint(
        module="account",
        action="tokenbalance",
        shape=ResponseShape.SCALAR,
        params=[ParamSpec("contractaddress", "contract_address"), ParamSpec("address"), ParamSpec("tag")],
    ),
    "get_historical_token_balance": Endpoint(
        module="account",
        action="tokenbalancehistory",
        shape=ResponseShape.SCALAR,
        params=[
            ParamSpec("contractaddress", "contract_address"),
            ParamSpec("address"),
            ParamSpec("blockno", "block_no"),
        ],
    ),
    "get_token_supply": Endpoint(
        module="stats",
        action="tokensupply",
        shape=ResponseShape.SCALAR,
        params=[ParamSpec("contractaddress", "contract_address")],
    ),
    "get_historical_token_supply": Endpoint(
        module="stats",
        action="tokensupplyhistory",
        shape=ResponseShape.SCALAR,
        params=[ParamSpec("contractaddress", "contract_address"), ParamSpec("blockno", "block_no")],
    ),
    "get_token_holder_list": Endpoint(
        module="token",
        action="tokenholderlist",
        shape=ResponseShape.LIST,
        model=TokenHolderEntry,
        params=[ParamSpec("contractaddress", "contract_address"), *_PAGINATION],
    ),
    "get_token_holder_count": Endpoint(
        module="token",
        action="tokenholdercount",
        shape=ResponseShape.SCALAR,
        params=[ParamSpec("contractaddress", "contract_address")],
    ),
    "get_token_info": Endpoint(
        module="token",
        action="tokeninfo",
        shape=ResponseShape.LIST,
        model=TokenInfo,
        params=[ParamSpec("contractaddress", "contract_address")],
    ),
    "get_top_token_holders": Endpoint(
        module="token",
        action="topholders",
        shape=ResponseShape.LIST,
        model=TopTokenHolder,
        params=[ParamSpec("contractaddress", "contract_address"), *_PAGINATION],
    ),
    # -- Gas ---------------------------------------------------------------
    "get_gas_oracle": Endpoint(
        module="gastracker",
        action="gasoracle",
        shape=ResponseShape.OBJECT,
        model=GasOracle,
        params=[],
    ),
    "get_gas_estimate": Endpoint(
        module="gastracker",
        action="gasestimate",
        shape=ResponseShape.SCALAR,
        params=[ParamSpec("gasprice", "gas_price")],
    ),
    # -- Stats -------------------------------------------------------------
    "get_eth_price": Endpoint(
        module="stats",
        action="ethprice",
        shape=ResponseShape.OBJECT,
        model=EthPrice,
        params=[],
    ),
    "get_eth_supply": Endpoint(
        module="stats",
        action="ethsupply",
        shape=ResponseShape.SCALAR,
        params=[],
    ),
    "get_eth_supply2": Endpoint(
        module="stats",
        action="ethsupply2",
        shape=ResponseShape.OBJECT,
        model=EthSupply2,
        params=[],
    ),
    "get_node_count": Endpoint(
        module="stats",
        action="nodecount",
        shape=ResponseShape.OBJECT,
        model=NodeCount,
        params=[],
    ),
    "get_daily_stats": Endpoint(
        module="stats",
        action="__dynamic__",
        shape=ResponseShape.LIST,
        model=DailyStatistic,
        params=[
            ParamSpec("startdate", "start_date"),
            ParamSpec("enddate", "end_date"),
            _SORT,
        ],
    ),
    "get_chain_size": Endpoint(
        module="stats",
        action="chainsize",
        shape=ResponseShape.LIST,
        model=DailyStatistic,
        params=[
            ParamSpec("startdate", "start_date"),
            ParamSpec("enddate", "end_date"),
            ParamSpec("clienttype", "client_type"),
            ParamSpec("syncmode", "sync_mode"),
            _SORT,
        ],
    ),
    "get_eth_daily_price": Endpoint(
        module="stats",
        action="ethdailyprice",
        shape=ResponseShape.LIST,
        model=DailyStatistic,
        params=[
            ParamSpec("startdate", "start_date"),
            ParamSpec("enddate", "end_date"),
            _SORT,
        ],
    ),
    "get_chainlist": Endpoint(
        module="chainlist",
        action="chainlist",
        shape=ResponseShape.LIST,
        model=ChainListEntry,
        params=[],
    ),
}
