"""Sync block explorer client with per-provider fallback.

Usage::

    with SyncBlockpartyClient(chain_id=8453) as client:
        response = client.get_internal_transactions(
            address="0x...", start_block=7775467, limit=10, sort="asc",
        )
        for tx in response.result:
            print(tx.hash, tx.value)

With shared providers::

    providers = ProviderSet([...])
    client_a = SyncBlockpartyClient(chain_id=8453, providers=providers)
    client_b = SyncBlockpartyClient(chain_id=42161, providers=providers)
"""

from __future__ import annotations

from typing import Any, Literal

from blockparty._types import ExplorerType
from blockparty.client._base import BlockpartyClientBase, emit_fallback_warning
from blockparty.client._endpoints import (
    ENDPOINT_REGISTRY,
    build_call_kwargs,
    parse_endpoint_response,
)
from blockparty.client._middleware import ResponseCache
from blockparty.client._transport import (
    SyncTransport,
    TransportError,
    TransportHTTPError,
    create_sync_transport,
    wrap_sync_transport,
)
from blockparty.exceptions import ExplorerNotFoundError, PoolExhaustedError
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
from blockparty.pool._base import ProviderSet, is_fallback_eligible
from blockparty.ratelimit.tiers import TierSpec
from blockparty.registry.chain_registry import ChainRegistry


class SyncBlockpartyClient(BlockpartyClientBase):
    """Sync client for EVM block explorer APIs.

    Supports provider fallback: when a :class:`~blockparty.pool._base.ProviderSet`
    with multiple credentials is used, transient errors on one provider
    automatically fall back to the next.

    Args:
        chain_id: The EVM chain ID (e.g. ``8453`` for Base).
        providers: A :class:`ProviderSet` with ordered credentials and
            shared rate limiting.  Mutually exclusive with ``explorer_type``
            / ``api_key`` / ``tier``.
        explorer_type: Explicit explorer type (creates a single-credential
            ProviderSet internally).
        api_key: API key for Etherscan-compatible providers.
        tier: Rate-limit tier for bucket configuration.
        http_backend: HTTP library: ``"requests"`` (default) or ``"httpx"``.
        transport: A pre-created ``requests.Session`` or
            ``httpx.Client``.  When provided, blockparty does NOT close
            it — the caller is responsible for lifecycle management.
        cache_ttl: Response cache TTL in seconds (0 disables).
        registry: Custom chain registry (bundled snapshot used if omitted).
    """

    def __init__(
        self,
        chain_id: int,
        *,
        providers: ProviderSet | None = None,
        explorer_type: ExplorerType | None = None,
        api_key: str | None = None,
        tier: TierSpec = None,
        http_backend: Literal["requests", "httpx"] = "requests",
        transport: Any = None,
        cache_ttl: int = 30,
        registry: ChainRegistry | None = None,
    ) -> None:
        super().__init__(
            chain_id,
            providers=providers,
            explorer_type=explorer_type,
            api_key=api_key,
            tier=tier,
            http_backend=http_backend,
            transport=transport,
            cache_ttl=cache_ttl,
            registry=registry,
        )
        # Transport — created lazily or wrapped from user-provided session.
        self._transport: SyncTransport | None = None
        self._owns_transport: bool = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _ensure_transport(self) -> SyncTransport:
        if self._transport is None:
            if self._user_transport is not None:
                self._transport = wrap_sync_transport(self._user_transport)
                self._owns_transport = False
            else:
                self._transport, self._owns_transport = create_sync_transport(
                    self._http_backend,
                )
        return self._transport

    def close(self) -> None:
        """Close the underlying HTTP session (if we own it)."""
        if self._transport is not None and self._owns_transport:
            self._transport.close()
        self._transport = None

    def __enter__(self) -> SyncBlockpartyClient:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Core execute with fallback
    # ------------------------------------------------------------------

    def _execute(
        self,
        ep_name: str,
        *,
        force_refresh: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Build params, try each provider with fallback, parse response.

        Rate limiting is enforced via the shared RateLimitBudget before
        each HTTP call.  The transport is a dumb pipe that sends GET
        requests and returns JSON.
        """
        ep = ENDPOINT_REGISTRY[ep_name]
        transport = self._ensure_transport()
        errors: list[tuple[ExplorerType, Exception]] = []

        for rp in self._resolved:
            # Build API params — maps Python names to API names, drops None.
            api_params = build_call_kwargs(ep, dict(kwargs))
            built = rp.backend.build_request_params(
                api_key=rp.credential.api_key,
                **api_params,
            )

            # Check cache.
            cache_key = ResponseCache.make_key(built)
            if not force_refresh:
                cached = self._cache.get(cache_key)
                if cached is not None:
                    result = parse_endpoint_response(ep, cached, rp.backend)
                    result.provider = rp.credential.type
                    return result

            # Rate limit — shared across all clients with same (provider, key).
            rp.budget.acquire_sync()

            # HTTP call.
            try:
                data = transport.request(
                    "GET",
                    rp.explorer_info.api_url,
                    params=built,
                )
            except TransportHTTPError as exc:
                if not is_fallback_eligible(exc):
                    raise
                errors.append((rp.credential.type, exc))
                emit_fallback_warning(rp, self._chain_id, exc)
                continue
            except TransportError as exc:
                errors.append((rp.credential.type, exc))
                emit_fallback_warning(rp, self._chain_id, exc)
                continue

            # Parse response — may raise ExplorerAPIError.
            try:
                result = parse_endpoint_response(ep, data, rp.backend)
            except Exception as exc:
                if not is_fallback_eligible(exc):
                    raise
                errors.append((rp.credential.type, exc))
                emit_fallback_warning(rp, self._chain_id, exc)
                continue

            self._cache.set(cache_key, data)
            result.provider = rp.credential.type
            return result

        if errors:
            raise PoolExhaustedError(errors)
        raise ExplorerNotFoundError(self._chain_id)

    # ------------------------------------------------------------------
    # Account endpoints
    # ------------------------------------------------------------------

    def get_normal_transactions(
        self,
        address: str,
        start_block: int = 0,
        end_block: int | None = None,
        page: int = 1,
        limit: int = 10,
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[NormalTransaction]:
        """Fetch normal transactions for an address."""
        return self._execute(
            "get_normal_transactions",
            force_refresh=force_refresh,
            address=address,
            start_block=start_block,
            end_block=end_block,
            page=page,
            limit=limit,
            sort=sort,
        )

    def get_internal_transactions(
        self,
        address: str,
        start_block: int = 0,
        end_block: int | None = None,
        page: int = 1,
        limit: int = 10,
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[InternalTransaction]:
        """Fetch internal (trace) transactions for an address."""
        return self._execute(
            "get_internal_transactions",
            force_refresh=force_refresh,
            address=address,
            start_block=start_block,
            end_block=end_block,
            page=page,
            limit=limit,
            sort=sort,
        )

    def get_internal_transactions_by_hash(
        self,
        txhash: str,
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[InternalTransaction]:
        """Fetch internal transactions for a specific transaction hash."""
        return self._execute(
            "get_internal_transactions_by_hash",
            force_refresh=force_refresh,
            txhash=txhash,
        )

    def get_internal_transactions_by_block_range(
        self,
        start_block: int = 0,
        end_block: int | None = None,
        page: int = 1,
        limit: int = 10,
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[InternalTransaction]:
        """Fetch internal transactions within a block range."""
        return self._execute(
            "get_internal_transactions_by_block_range",
            force_refresh=force_refresh,
            start_block=start_block,
            end_block=end_block,
            page=page,
            limit=limit,
            sort=sort,
        )

    def get_erc20_token_transfers(
        self,
        address: str | None = None,
        contract_address: str | None = None,
        start_block: int = 0,
        end_block: int | None = None,
        page: int = 1,
        limit: int = 10,
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[ERC20TokenTransfer]:
        """Fetch ERC-20 token transfers for an address and/or contract."""
        return self._execute(
            "get_erc20_token_transfers",
            force_refresh=force_refresh,
            address=address,
            contract_address=contract_address,
            start_block=start_block,
            end_block=end_block,
            page=page,
            limit=limit,
            sort=sort,
        )

    def get_erc721_token_transfers(
        self,
        address: str | None = None,
        contract_address: str | None = None,
        start_block: int = 0,
        end_block: int | None = None,
        page: int = 1,
        limit: int = 10,
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[ERC721TokenTransfer]:
        """Fetch ERC-721 (NFT) token transfers."""
        return self._execute(
            "get_erc721_token_transfers",
            force_refresh=force_refresh,
            address=address,
            contract_address=contract_address,
            start_block=start_block,
            end_block=end_block,
            page=page,
            limit=limit,
            sort=sort,
        )

    def get_erc1155_token_transfers(
        self,
        address: str | None = None,
        contract_address: str | None = None,
        start_block: int = 0,
        end_block: int | None = None,
        page: int = 1,
        limit: int = 10,
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[ERC1155TokenTransfer]:
        """Fetch ERC-1155 token transfers."""
        return self._execute(
            "get_erc1155_token_transfers",
            force_refresh=force_refresh,
            address=address,
            contract_address=contract_address,
            start_block=start_block,
            end_block=end_block,
            page=page,
            limit=limit,
            sort=sort,
        )

    def get_balance(
        self,
        address: str | list[str],
        tag: str = "latest",
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Fetch native token balance for one or more addresses (up to 20)."""
        return self._execute(
            "get_balance",
            force_refresh=force_refresh,
            address=address,
            tag=tag,
        )

    def get_historical_balance(
        self,
        address: str,
        block_no: int,
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Fetch historical native balance at a specific block."""
        return self._execute(
            "get_historical_balance",
            force_refresh=force_refresh,
            address=address,
            block_no=block_no,
        )

    def get_address_token_balance(
        self,
        address: str,
        page: int = 1,
        limit: int = 10,
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[AddressTokenBalance]:
        """Fetch ERC-20 token holdings for an address."""
        return self._execute(
            "get_address_token_balance",
            force_refresh=force_refresh,
            address=address,
            page=page,
            limit=limit,
        )

    def get_address_nft_inventory(
        self,
        address: str,
        contract_address: str,
        page: int = 1,
        limit: int = 10,
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[AddressNFTInventory]:
        """Fetch ERC-721 token inventory for an address by contract."""
        return self._execute(
            "get_address_nft_inventory",
            force_refresh=force_refresh,
            address=address,
            contract_address=contract_address,
            page=page,
            limit=limit,
        )

    def get_mined_blocks(
        self,
        address: str,
        block_type: str = "blocks",
        page: int = 1,
        limit: int = 10,
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[MinedBlock]:
        """Fetch blocks validated by an address."""
        return self._execute(
            "get_mined_blocks",
            force_refresh=force_refresh,
            address=address,
            block_type=block_type,
            page=page,
            limit=limit,
        )

    def get_beacon_withdrawals(
        self,
        address: str,
        start_block: int = 0,
        end_block: int | None = None,
        page: int = 1,
        limit: int = 10,
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[BeaconWithdrawal]:
        """Fetch beacon chain withdrawals for an address."""
        return self._execute(
            "get_beacon_withdrawals",
            force_refresh=force_refresh,
            address=address,
            start_block=start_block,
            end_block=end_block,
            page=page,
            limit=limit,
            sort=sort,
        )

    def get_funded_by(
        self,
        address: str,
        *,
        force_refresh: bool = False,
    ) -> ObjectResponse[FundedBy]:
        """Fetch the address and transaction that first funded an EOA."""
        return self._execute(
            "get_funded_by",
            force_refresh=force_refresh,
            address=address,
        )

    def get_deposit_transactions(
        self,
        address: str,
        page: int = 1,
        limit: int = 10,
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[DepositTransaction]:
        """Fetch deposit transactions for an address (L2 chains)."""
        return self._execute(
            "get_deposit_transactions",
            force_refresh=force_refresh,
            address=address,
            page=page,
            limit=limit,
            sort=sort,
        )

    def get_withdrawal_transactions(
        self,
        address: str,
        page: int = 1,
        limit: int = 10,
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[dict[str, Any]]:
        """Fetch withdrawal transactions for an address."""
        return self._execute(
            "get_withdrawal_transactions",
            force_refresh=force_refresh,
            address=address,
            page=page,
            limit=limit,
            sort=sort,
        )

    def get_plasma_deposits(
        self,
        address: str,
        page: int = 1,
        limit: int = 10,
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[PlasmaDeposit]:
        """Fetch Plasma deposit transactions for an address."""
        return self._execute(
            "get_plasma_deposits",
            force_refresh=force_refresh,
            address=address,
            page=page,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # Contract endpoints
    # ------------------------------------------------------------------

    def get_contract_abi(
        self,
        address: str,
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Fetch the ABI for a verified smart contract."""
        return self._execute(
            "get_contract_abi",
            force_refresh=force_refresh,
            address=address,
        )

    def get_contract_source_code(
        self,
        address: str,
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[ContractSourceCode]:
        """Fetch source code for a verified smart contract."""
        return self._execute(
            "get_contract_source_code",
            force_refresh=force_refresh,
            address=address,
        )

    def get_contract_creation(
        self,
        contract_addresses: str | list[str],
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[ContractCreation]:
        """Fetch contract creator and creation tx (up to 5 addresses)."""
        return self._execute(
            "get_contract_creation",
            force_refresh=force_refresh,
            contract_addresses=contract_addresses,
        )

    # ------------------------------------------------------------------
    # Transaction endpoints
    # ------------------------------------------------------------------

    def get_transaction_status(
        self,
        txhash: str,
        *,
        force_refresh: bool = False,
    ) -> ObjectResponse[TransactionStatus]:
        """Check contract execution status of a transaction."""
        return self._execute(
            "get_transaction_status",
            force_refresh=force_refresh,
            txhash=txhash,
        )

    def get_transaction_receipt_status(
        self,
        txhash: str,
        *,
        force_refresh: bool = False,
    ) -> ObjectResponse[TransactionReceiptStatus]:
        """Check transaction receipt status."""
        return self._execute(
            "get_transaction_receipt_status",
            force_refresh=force_refresh,
            txhash=txhash,
        )

    # ------------------------------------------------------------------
    # Block endpoints
    # ------------------------------------------------------------------

    def get_block_reward(
        self,
        block_no: int,
        *,
        force_refresh: bool = False,
    ) -> ObjectResponse[BlockReward]:
        """Fetch block and uncle rewards by block number."""
        return self._execute(
            "get_block_reward",
            force_refresh=force_refresh,
            block_no=block_no,
        )

    def get_block_countdown(
        self,
        block_no: int,
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Fetch estimated countdown time to a block."""
        return self._execute(
            "get_block_countdown",
            force_refresh=force_refresh,
            block_no=block_no,
        )

    def get_block_no_by_time(
        self,
        timestamp: int,
        closest: Literal["before", "after"] = "before",
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Fetch block number mined at a specific timestamp."""
        return self._execute(
            "get_block_no_by_time",
            force_refresh=force_refresh,
            timestamp=timestamp,
            closest=closest,
        )

    # ------------------------------------------------------------------
    # Logs endpoints
    # ------------------------------------------------------------------

    def get_logs(
        self,
        address: str | None = None,
        from_block: int = 0,
        to_block: int | None = None,
        topic0: str | None = None,
        topic1: str | None = None,
        topic2: str | None = None,
        topic3: str | None = None,
        topic0_1_opr: Literal["and", "or"] | None = None,
        topic0_2_opr: Literal["and", "or"] | None = None,
        topic0_3_opr: Literal["and", "or"] | None = None,
        topic1_2_opr: Literal["and", "or"] | None = None,
        topic1_3_opr: Literal["and", "or"] | None = None,
        topic2_3_opr: Literal["and", "or"] | None = None,
        page: int = 1,
        limit: int = 1000,
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[EventLog]:
        """Fetch event logs with optional address and topic filters."""
        return self._execute(
            "get_logs",
            force_refresh=force_refresh,
            address=address,
            from_block=from_block,
            to_block=to_block,
            topic0=topic0,
            topic1=topic1,
            topic2=topic2,
            topic3=topic3,
            topic0_1_opr=topic0_1_opr,
            topic0_2_opr=topic0_2_opr,
            topic0_3_opr=topic0_3_opr,
            topic1_2_opr=topic1_2_opr,
            topic1_3_opr=topic1_3_opr,
            topic2_3_opr=topic2_3_opr,
            page=page,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # Token endpoints
    # ------------------------------------------------------------------

    def get_token_balance(
        self,
        contract_address: str,
        address: str,
        tag: str = "latest",
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Fetch ERC-20 token balance for an address."""
        return self._execute(
            "get_token_balance",
            force_refresh=force_refresh,
            contract_address=contract_address,
            address=address,
            tag=tag,
        )

    def get_historical_token_balance(
        self,
        contract_address: str,
        address: str,
        block_no: int,
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Fetch historical ERC-20 token balance at a specific block."""
        return self._execute(
            "get_historical_token_balance",
            force_refresh=force_refresh,
            contract_address=contract_address,
            address=address,
            block_no=block_no,
        )

    def get_token_supply(
        self,
        contract_address: str,
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Fetch total supply of an ERC-20 token."""
        return self._execute(
            "get_token_supply",
            force_refresh=force_refresh,
            contract_address=contract_address,
        )

    def get_historical_token_supply(
        self,
        contract_address: str,
        block_no: int,
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Fetch historical total supply of an ERC-20 token at a block."""
        return self._execute(
            "get_historical_token_supply",
            force_refresh=force_refresh,
            contract_address=contract_address,
            block_no=block_no,
        )

    def get_token_holder_list(
        self,
        contract_address: str,
        page: int = 1,
        limit: int = 10,
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[TokenHolderEntry]:
        """Fetch list of token holders for a contract."""
        return self._execute(
            "get_token_holder_list",
            force_refresh=force_refresh,
            contract_address=contract_address,
            page=page,
            limit=limit,
        )

    def get_token_holder_count(
        self,
        contract_address: str,
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Fetch count of token holders for a contract."""
        return self._execute(
            "get_token_holder_count",
            force_refresh=force_refresh,
            contract_address=contract_address,
        )

    def get_token_info(
        self,
        contract_address: str,
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[TokenInfo]:
        """Fetch token project info and social links."""
        return self._execute(
            "get_token_info",
            force_refresh=force_refresh,
            contract_address=contract_address,
        )

    def get_top_token_holders(
        self,
        contract_address: str,
        limit: int = 10,
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[TopTokenHolder]:
        """Fetch top token holders for a contract."""
        return self._execute(
            "get_top_token_holders",
            force_refresh=force_refresh,
            contract_address=contract_address,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # Gas tracker endpoints
    # ------------------------------------------------------------------

    def get_gas_oracle(
        self,
        *,
        force_refresh: bool = False,
    ) -> ObjectResponse[GasOracle]:
        """Fetch current gas price recommendations."""
        return self._execute("get_gas_oracle", force_refresh=force_refresh)

    def get_gas_estimate(
        self,
        gas_price: int,
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Estimate confirmation time for a given gas price."""
        return self._execute(
            "get_gas_estimate",
            force_refresh=force_refresh,
            gas_price=gas_price,
        )

    # ------------------------------------------------------------------
    # Stats endpoints
    # ------------------------------------------------------------------

    def get_eth_price(
        self,
        *,
        force_refresh: bool = False,
    ) -> ObjectResponse[EthPrice]:
        """Fetch latest native token price."""
        return self._execute("get_eth_price", force_refresh=force_refresh)

    def get_eth_supply(
        self,
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Fetch current circulating supply of Ether."""
        return self._execute("get_eth_supply", force_refresh=force_refresh)

    def get_eth_supply2(
        self,
        *,
        force_refresh: bool = False,
    ) -> ObjectResponse[EthSupply2]:
        """Fetch extended Ether supply including staking and burns."""
        return self._execute("get_eth_supply2", force_refresh=force_refresh)

    def get_node_count(
        self,
        *,
        force_refresh: bool = False,
    ) -> ObjectResponse[NodeCount]:
        """Fetch total Ethereum node count."""
        return self._execute("get_node_count", force_refresh=force_refresh)

    def get_daily_stats(
        self,
        action: str,
        start_date: str,
        end_date: str,
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[DailyStatistic]:
        """Fetch daily statistics (e.g. ``"dailyavgblocksize"``, ``"dailytx"``)."""
        return self._execute(
            "get_daily_stats",
            force_refresh=force_refresh,
            action=action,
            start_date=start_date,
            end_date=end_date,
            sort=sort,
        )

    def get_chain_size(
        self,
        start_date: str,
        end_date: str,
        client_type: str = "geth",
        sync_mode: str = "default",
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[DailyStatistic]:
        """Fetch Ethereum blockchain size over a date range."""
        return self._execute(
            "get_chain_size",
            force_refresh=force_refresh,
            start_date=start_date,
            end_date=end_date,
            client_type=client_type,
            sync_mode=sync_mode,
            sort=sort,
        )

    def get_eth_daily_price(
        self,
        start_date: str,
        end_date: str,
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[DailyStatistic]:
        """Fetch historical Ether price data."""
        return self._execute(
            "get_eth_daily_price",
            force_refresh=force_refresh,
            start_date=start_date,
            end_date=end_date,
            sort=sort,
        )

    def get_chainlist(
        self,
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[ChainListEntry]:
        """Fetch the list of supported Etherscan chains."""
        return self._execute("get_chainlist", force_refresh=force_refresh)
