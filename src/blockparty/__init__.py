"""blockparty — A unified Python client for EVM block explorer APIs.

Supports Etherscan, Routescan, and Blockscout with normalized responses,
sync/async clients, connection pooling with fallback, and frontend URL builders.
"""

from blockparty._types import CoercedInt, ExplorerType
from blockparty.client.async_client import AsyncBlockpartyClient
from blockparty.client.sync_client import SyncBlockpartyClient
from blockparty.exceptions import (
    BlockpartyError,
    ChainNotFoundError,
    ChainNotSupportedError,
    ConfigurationError,
    ExplorerAPIError,
    ExplorerNotFoundError,
    InvalidAddressError,
    InvalidAPIKeyError,
    PoolExhaustedError,
    PremiumEndpointError,
    RateLimitError,
)
from blockparty.models.registry import ChainEntry, ExplorerInfo
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
    ExplorerResponse,
    FundedBy,
    GasOracle,
    InternalTransaction,
    MinedBlock,
    NodeCount,
    NormalTransaction,
    ObjectResponse,
    PlasmaDeposit,
    ScalarResponse,
    TokenHolderEntry,
    TokenInfo,
    TopTokenHolder,
    TransactionReceiptStatus,
    TransactionStatus,
)
from blockparty.pool._base import ProviderCredential, ProviderSet
from blockparty.pool.async_pool import AsyncBlockpartyPool
from blockparty.pool.sync_pool import SyncBlockpartyPool
from blockparty.ratelimit.tiers import (
    BlockscoutTier,
    CustomRateLimit,
    EtherscanTier,
    RoutescanTier,
)
from blockparty.registry.chain_registry import ChainRegistry
from blockparty.urls.builder import ExplorerURLs
from blockparty.warnings import AuthFallbackWarning, BlockpartyWarning, FallbackWarning

__all__ = [
    # Clients
    "AsyncBlockpartyClient",
    "SyncBlockpartyClient",
    # Pools
    "AsyncBlockpartyPool",
    "SyncBlockpartyPool",
    # Provider configuration
    "ProviderCredential",
    "ProviderSet",
    # Types
    "CoercedInt",
    "ExplorerType",
    # Response models — envelopes
    "ExplorerResponse",
    "ObjectResponse",
    "ScalarResponse",
    # Response models — account
    "NormalTransaction",
    "InternalTransaction",
    "ERC20TokenTransfer",
    "ERC721TokenTransfer",
    "ERC1155TokenTransfer",
    "AddressTokenBalance",
    "AddressNFTInventory",
    "MinedBlock",
    "BeaconWithdrawal",
    "FundedBy",
    "DepositTransaction",
    "PlasmaDeposit",
    # Response models — contract
    "ContractCreation",
    "ContractSourceCode",
    # Response models — transaction
    "TransactionStatus",
    "TransactionReceiptStatus",
    # Response models — block
    "BlockReward",
    # Response models — logs
    "EventLog",
    # Response models — gas
    "GasOracle",
    # Response models — stats / token
    "EthPrice",
    "EthSupply2",
    "NodeCount",
    "DailyStatistic",
    "ChainListEntry",
    "TokenHolderEntry",
    "TopTokenHolder",
    "TokenInfo",
    # Registry
    "ChainEntry",
    "ExplorerInfo",
    "ChainRegistry",
    # URL builder
    "ExplorerURLs",
    # Rate limiting
    "BlockscoutTier",
    "CustomRateLimit",
    "EtherscanTier",
    "RoutescanTier",
    # Exceptions
    "BlockpartyError",
    "ChainNotFoundError",
    "ChainNotSupportedError",
    "ConfigurationError",
    "ExplorerAPIError",
    "ExplorerNotFoundError",
    "InvalidAPIKeyError",
    "InvalidAddressError",
    "PoolExhaustedError",
    "PremiumEndpointError",
    "RateLimitError",
    # Warnings
    "AuthFallbackWarning",
    "BlockpartyWarning",
    "FallbackWarning",
]
