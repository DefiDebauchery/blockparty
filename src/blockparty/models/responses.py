"""Normalized response models for block explorer APIs.

All numeric-string fields from the raw API responses are coerced to native
Python ``int`` via :data:`~blockparty._types.CoercedInt`.  Field names are
normalized across providers (e.g., Blockscout's ``transactionHash`` becomes
``hash``).

Normalization of provider-specific field names happens in each
:class:`~blockparty.backends._base.ExplorerBackend` *before* Pydantic
validation, so these models represent the unified schema.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from blockparty._types import CoercedInt, ExplorerType

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Generic response envelope
# ---------------------------------------------------------------------------


class ExplorerResponse(BaseModel, Generic[T]):
    """Wrapper for the explorer API response envelope.

    The ``status`` field is present on Etherscan and Routescan (``"1"`` for
    success, ``"0"`` for error) but absent on Blockscout.

    The ``provider`` field is set by the client after a successful API call
    and indicates which explorer backend actually served the response.  It
    is ``None`` when the response was constructed directly (e.g. in tests).
    """

    status: str | None = None
    message: str
    result: list[T]
    provider: ExplorerType | None = None


class ScalarResponse(BaseModel):
    """Wrapper for API responses whose ``result`` is a single scalar value."""

    status: str | None = None
    message: str
    result: str
    provider: ExplorerType | None = None


class ObjectResponse(BaseModel, Generic[T]):
    """Wrapper for API responses whose ``result`` is a single object."""

    status: str | None = None
    message: str
    result: T
    provider: ExplorerType | None = None


# ---------------------------------------------------------------------------
# Account module
# ---------------------------------------------------------------------------


class NormalTransaction(BaseModel):
    """A normal (external) transaction."""

    model_config = ConfigDict(populate_by_name=True)

    block_number: CoercedInt = Field(alias="blockNumber")
    block_hash: str = Field(alias="blockHash")
    timestamp: CoercedInt = Field(alias="timeStamp")
    hash: str
    nonce: CoercedInt
    transaction_index: CoercedInt = Field(alias="transactionIndex")
    from_address: str = Field(alias="from")
    to_address: str = Field(alias="to")
    value: CoercedInt
    gas: CoercedInt
    gas_price: CoercedInt = Field(alias="gasPrice")
    input: str
    method_id: str = Field(default="", alias="methodId")
    function_name: str = Field(default="", alias="functionName")
    contract_address: str = Field(alias="contractAddress")
    cumulative_gas_used: CoercedInt = Field(alias="cumulativeGasUsed")
    txreceipt_status: str = Field(default="", alias="txreceipt_status")
    gas_used: CoercedInt = Field(alias="gasUsed")
    confirmations: CoercedInt
    is_error: bool = Field(alias="isError")


class InternalTransaction(BaseModel):
    """A normalized internal (trace) transaction from any explorer backend.

    Fields present on all providers are required.  Fields that are
    provider-specific (``trace_id`` for Etherscan/Routescan, ``index`` for
    Blockscout) are optional.
    """

    model_config = ConfigDict(populate_by_name=True)

    block_number: CoercedInt = Field(alias="blockNumber")
    timestamp: CoercedInt = Field(alias="timeStamp")
    hash: str = Field(description="Transaction hash. Sourced from 'hash' (ES/RS) or 'transactionHash' (BS).")
    from_address: str = Field(alias="from")
    to_address: str = Field(alias="to")
    value: CoercedInt = Field(description="Value transferred in wei.")
    contract_address: str = Field(alias="contractAddress")
    input: str
    type: str = Field(
        description="Internal call type (e.g., 'call', 'delegatecall'). Sourced from 'type' (ES/RS) or 'callType' (BS)."
    )
    gas: CoercedInt
    gas_used: CoercedInt = Field(alias="gasUsed")
    is_error: bool = Field(alias="isError")
    error_code: str = Field(alias="errCode")

    # Provider-specific — NOT analogous to each other
    trace_id: str | None = Field(default=None, alias="traceId")
    """Etherscan / Routescan only.  Hierarchical trace identifier (e.g., ``"0_1_1"``)."""

    index: str | None = Field(default=None)
    """Blockscout only.  Positional index of the internal transaction."""


class ERC20TokenTransfer(BaseModel):
    """An ERC-20 token transfer event."""

    model_config = ConfigDict(populate_by_name=True)

    block_number: CoercedInt = Field(alias="blockNumber")
    timestamp: CoercedInt = Field(alias="timeStamp")
    hash: str
    nonce: CoercedInt
    block_hash: str = Field(alias="blockHash")
    from_address: str = Field(alias="from")
    contract_address: str = Field(alias="contractAddress")
    to_address: str = Field(alias="to")
    value: CoercedInt
    token_name: str = Field(alias="tokenName")
    token_symbol: str = Field(alias="tokenSymbol")
    token_decimal: CoercedInt = Field(alias="tokenDecimal")
    transaction_index: CoercedInt = Field(alias="transactionIndex")
    gas: CoercedInt
    gas_price: CoercedInt = Field(alias="gasPrice")
    gas_used: CoercedInt = Field(alias="gasUsed")
    cumulative_gas_used: CoercedInt = Field(alias="cumulativeGasUsed")
    input: str
    method_id: str = Field(default="", alias="methodId")
    function_name: str = Field(default="", alias="functionName")
    confirmations: CoercedInt


class ERC721TokenTransfer(BaseModel):
    """An ERC-721 (NFT) token transfer event."""

    model_config = ConfigDict(populate_by_name=True)

    block_number: CoercedInt = Field(alias="blockNumber")
    timestamp: CoercedInt = Field(alias="timeStamp")
    hash: str
    nonce: CoercedInt
    block_hash: str = Field(alias="blockHash")
    from_address: str = Field(alias="from")
    contract_address: str = Field(alias="contractAddress")
    to_address: str = Field(alias="to")
    token_id: str = Field(alias="tokenID")
    token_name: str = Field(alias="tokenName")
    token_symbol: str = Field(alias="tokenSymbol")
    token_decimal: CoercedInt = Field(alias="tokenDecimal")
    transaction_index: CoercedInt = Field(alias="transactionIndex")
    gas: CoercedInt
    gas_price: CoercedInt = Field(alias="gasPrice")
    gas_used: CoercedInt = Field(alias="gasUsed")
    cumulative_gas_used: CoercedInt = Field(alias="cumulativeGasUsed")
    input: str
    method_id: str = Field(default="", alias="methodId")
    function_name: str = Field(default="", alias="functionName")
    confirmations: CoercedInt


class ERC1155TokenTransfer(BaseModel):
    """An ERC-1155 token transfer event."""

    model_config = ConfigDict(populate_by_name=True)

    block_number: CoercedInt = Field(alias="blockNumber")
    timestamp: CoercedInt = Field(alias="timeStamp")
    hash: str
    nonce: CoercedInt
    block_hash: str = Field(alias="blockHash")
    transaction_index: CoercedInt = Field(alias="transactionIndex")
    gas: CoercedInt
    gas_price: CoercedInt = Field(alias="gasPrice")
    gas_used: CoercedInt = Field(alias="gasUsed")
    cumulative_gas_used: CoercedInt = Field(alias="cumulativeGasUsed")
    input: str
    method_id: str = Field(default="", alias="methodId")
    function_name: str = Field(default="", alias="functionName")
    contract_address: str = Field(alias="contractAddress")
    from_address: str = Field(alias="from")
    to_address: str = Field(alias="to")
    token_id: str = Field(alias="tokenID")
    token_value: CoercedInt = Field(alias="tokenValue")
    token_name: str = Field(alias="tokenName")
    token_symbol: str = Field(alias="tokenSymbol")
    confirmations: CoercedInt


class AddressTokenBalance(BaseModel):
    """ERC-20 token holding for an address."""

    model_config = ConfigDict(populate_by_name=True)

    token_address: str = Field(alias="TokenAddress")
    token_name: str = Field(alias="TokenName")
    token_symbol: str = Field(alias="TokenSymbol")
    token_quantity: str = Field(alias="TokenQuantity")
    token_divisor: str = Field(alias="TokenDivisor")
    token_price_usd: str = Field(default="", alias="TokenPriceUSD")


class AddressNFTInventory(BaseModel):
    """ERC-721 token inventory entry."""

    model_config = ConfigDict(populate_by_name=True)

    token_address: str = Field(alias="TokenAddress")
    token_id: str = Field(alias="TokenId")


class MinedBlock(BaseModel):
    """A block validated by an address."""

    model_config = ConfigDict(populate_by_name=True)

    block_number: CoercedInt = Field(alias="blockNumber")
    timestamp: CoercedInt = Field(alias="timeStamp")
    block_reward: str = Field(alias="blockReward")


class BeaconWithdrawal(BaseModel):
    """A beacon chain withdrawal transaction."""

    model_config = ConfigDict(populate_by_name=True)

    withdrawal_index: CoercedInt = Field(alias="withdrawalIndex")
    validator_index: CoercedInt = Field(alias="validatorIndex")
    address: str
    amount: CoercedInt
    block_number: CoercedInt = Field(alias="blockNumber")
    timestamp: CoercedInt


class FundedBy(BaseModel):
    """Address funding origin info."""

    model_config = ConfigDict(populate_by_name=True)

    block: CoercedInt
    timestamp: CoercedInt = Field(alias="timeStamp")
    funding_address: str = Field(alias="fundingAddress")
    funding_txn: str = Field(alias="fundingTxn")
    value: CoercedInt


class DepositTransaction(BaseModel):
    """A deposit transaction (L2 chains)."""

    model_config = ConfigDict(populate_by_name=True)

    block_number: CoercedInt = Field(alias="blockNumber")
    timestamp: CoercedInt = Field(alias="timeStamp")
    block_hash: str = Field(alias="blockHash")
    hash: str
    nonce: CoercedInt
    from_address: str = Field(alias="from")
    to_address: str = Field(alias="to")
    value: CoercedInt
    gas: CoercedInt
    gas_price: CoercedInt = Field(alias="gasPrice")
    input: str
    cumulative_gas_used: CoercedInt = Field(alias="cumulativeGasUsed")
    gas_used: CoercedInt = Field(alias="gasUsed")
    is_error: str = Field(alias="isError")
    txreceipt_status: str = Field(default="", alias="txreceipt_status")


class PlasmaDeposit(BaseModel):
    """A Plasma deposit transaction."""

    model_config = ConfigDict(populate_by_name=True)

    hash: str
    block_number: CoercedInt = Field(alias="blockNumber")
    timestamp: CoercedInt = Field(alias="timeStamp")
    from_address: str = Field(alias="from")
    address: str
    amount: CoercedInt
    token_name: str = Field(alias="tokenName")
    symbol: str
    contract_address: str = Field(alias="contractAddress")
    divisor: str


# ---------------------------------------------------------------------------
# Contract module
# ---------------------------------------------------------------------------


class ContractCreation(BaseModel):
    """Contract creator and creation tx info."""

    model_config = ConfigDict(populate_by_name=True)

    contract_address: str = Field(alias="contractAddress")
    contract_creator: str = Field(alias="contractCreator")
    tx_hash: str = Field(alias="txHash")
    block_number: CoercedInt = Field(alias="blockNumber")
    timestamp: CoercedInt
    contract_factory: str = Field(default="", alias="contractFactory")
    creation_bytecode: str = Field(default="", alias="creationBytecode")


class ContractSourceCode(BaseModel):
    """Verified contract source code information."""

    model_config = ConfigDict(populate_by_name=True)

    source_code: str = Field(alias="SourceCode")
    abi: str = Field(alias="ABI")
    contract_name: str = Field(alias="ContractName")
    compiler_version: str = Field(alias="CompilerVersion")
    compiler_type: str = Field(default="", alias="CompilerType")
    optimization_used: str = Field(alias="OptimizationUsed")
    runs: CoercedInt = Field(alias="Runs")
    constructor_arguments: str = Field(alias="ConstructorArguments")
    evm_version: str = Field(alias="EVMVersion")
    library: str = Field(alias="Library")
    license_type: str = Field(alias="LicenseType")
    proxy: str = Field(alias="Proxy")
    implementation: str = Field(alias="Implementation")
    swarm_source: str = Field(default="", alias="SwarmSource")


# ---------------------------------------------------------------------------
# Transaction module
# ---------------------------------------------------------------------------


class TransactionStatus(BaseModel):
    """Contract execution status for a transaction."""

    model_config = ConfigDict(populate_by_name=True)

    is_error: str = Field(alias="isError")
    err_description: str = Field(default="", alias="errDescription")


class TransactionReceiptStatus(BaseModel):
    """Transaction receipt status."""

    status: str


# ---------------------------------------------------------------------------
# Block module
# ---------------------------------------------------------------------------


class BlockReward(BaseModel):
    """Block and uncle rewards."""

    model_config = ConfigDict(populate_by_name=True)

    block_number: CoercedInt = Field(alias="blockNumber")
    timestamp: CoercedInt = Field(alias="timeStamp")
    block_miner: str = Field(alias="blockMiner")
    block_reward: str = Field(alias="blockReward")
    uncles: list[dict[str, str]]
    uncle_inclusion_reward: str = Field(alias="uncleInclusionReward")


# ---------------------------------------------------------------------------
# Logs module
# ---------------------------------------------------------------------------


class EventLog(BaseModel):
    """An event log entry."""

    model_config = ConfigDict(populate_by_name=True)

    address: str
    topics: list[str]
    data: str
    block_number: CoercedInt = Field(alias="blockNumber")
    block_hash: str = Field(alias="blockHash")
    timestamp: CoercedInt = Field(alias="timeStamp")
    gas_price: CoercedInt = Field(alias="gasPrice")
    gas_used: CoercedInt = Field(alias="gasUsed")
    log_index: CoercedInt = Field(alias="logIndex")
    transaction_hash: str = Field(alias="transactionHash")
    transaction_index: CoercedInt = Field(alias="transactionIndex")


# ---------------------------------------------------------------------------
# Gas tracker module
# ---------------------------------------------------------------------------


class GasOracle(BaseModel):
    """Current gas price recommendations."""

    model_config = ConfigDict(populate_by_name=True)

    last_block: str = Field(alias="LastBlock")
    safe_gas_price: str = Field(alias="SafeGasPrice")
    propose_gas_price: str = Field(alias="ProposeGasPrice")
    fast_gas_price: str = Field(alias="FastGasPrice")
    suggest_base_fee: str = Field(default="", alias="suggestBaseFee")
    gas_used_ratio: str = Field(default="", alias="gasUsedRatio")


# ---------------------------------------------------------------------------
# Stats module
# ---------------------------------------------------------------------------


class EthPrice(BaseModel):
    """Current native token price."""

    model_config = ConfigDict(populate_by_name=True)

    ethbtc: str
    ethbtc_timestamp: str
    ethusd: str
    ethusd_timestamp: str


class EthSupply2(BaseModel):
    """Extended Ether supply info."""

    model_config = ConfigDict(populate_by_name=True)

    eth_supply: str = Field(alias="EthSupply")
    eth2_staking: str = Field(alias="Eth2Staking")
    burnt_fees: str = Field(alias="BurntFees")
    withdrawn_total: str = Field(alias="WithdrawnTotal")


class NodeCount(BaseModel):
    """Total Ethereum node count."""

    model_config = ConfigDict(populate_by_name=True)

    utc_date: str = Field(alias="UTCDate")
    total_node_count: CoercedInt = Field(alias="TotalNodeCount")


class DailyStatistic(BaseModel):
    """Generic daily statistic entry used by multiple stats endpoints.

    The ``value`` field contains the stat-specific metric.  Use the endpoint
    context to interpret what it represents (block size, gas price, etc.).
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    utc_date: str = Field(alias="UTCDate")
    unix_timestamp: CoercedInt = Field(alias="unixTimeStamp")


class ChainListEntry(BaseModel):
    """A chain from the Etherscan chainlist endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    chainname: str
    chainid: str
    blockexplorer: str
    apiurl: str
    status: str
    comment: str = ""


# ---------------------------------------------------------------------------
# Token module
# ---------------------------------------------------------------------------


class TokenHolderEntry(BaseModel):
    """A token holder from the token holder list endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    token_holder_address: str = Field(alias="TokenHolderAddress")
    token_holder_quantity: str = Field(alias="TokenHolderQuantity")


class TopTokenHolder(BaseModel):
    """A top token holder entry."""

    model_config = ConfigDict(populate_by_name=True)

    token_holder_address: str = Field(alias="TokenHolderAddress")
    token_holder_quantity: str = Field(alias="TokenHolderQuantity")
    token_holder_address_type: str = Field(default="", alias="TokenHolderAddressType")


class TokenInfo(BaseModel):
    """Token project information and social links."""

    model_config = ConfigDict(populate_by_name=True)

    contract_address: str = Field(alias="contractAddress")
    token_name: str = Field(alias="tokenName")
    symbol: str
    divisor: str
    token_type: str = Field(alias="tokenType")
    total_supply: str = Field(alias="totalSupply")
    blue_checkmark: str = Field(default="", alias="blueCheckmark")
    description: str = ""
    website: str = ""
    email: str = ""
    blog: str = ""
    reddit: str = ""
    slack: str = ""
    facebook: str = ""
    twitter: str = ""
    bitcointalk: str = ""
    github: str = ""
    telegram: str = ""
    wechat: str = ""
    linkedin: str = ""
    discord: str = ""
    whitepaper: str = ""
    token_price_usd: str = Field(default="", alias="tokenPriceUSD")
    image: str = ""
