"""Async connection pool — convenience wrapper over ProviderSet.

Creates and caches :class:`AsyncBlockpartyClient` instances per chain.
All the real logic (fallback, rate limiting, credential resolution) lives
in the client via :class:`ProviderSet`.

Usage::

    async with AsyncBlockpartyPool(
        credentials=[
            ProviderCredential(type="etherscan", api_key="KEY", tier=EtherscanTier.STANDARD),
            ProviderCredential(type="routescan", tier=RoutescanTier.ANONYMOUS),
            ProviderCredential(type="blockscout"),
        ],
    ) as pool:
        response = await pool.get_internal_transactions(chain_id=8453, address="0x...")
"""

from __future__ import annotations

from typing import Any, Literal

from blockparty.client.async_client import AsyncBlockpartyClient
from blockparty.models.responses import (
    ContractSourceCode,
    EthPrice,
    EventLog,
    ExplorerResponse,
    GasOracle,
    InternalTransaction,
    NormalTransaction,
    ObjectResponse,
    ScalarResponse,
)
from blockparty.pool._base import BlockpartyPoolBase, ProviderCredential, ProviderSet
from blockparty.registry.chain_registry import ChainRegistry


class AsyncBlockpartyPool(BlockpartyPoolBase):
    """Async connection pool — multi-chain, multi-credential, fallback-aware.

    Creates and caches :class:`AsyncBlockpartyClient` instances per chain.
    All credentials, rate limiting, and fallback are managed by the shared
    :class:`ProviderSet`.

    Args:
        credentials: Ordered list of provider credentials.
        providers: A pre-built :class:`ProviderSet` (alternative to *credentials*).
        http_backend: HTTP library to use: ``"aiohttp"`` (default) or ``"httpx"``.
        cache_ttl: Response cache TTL passed to created clients.
        registry: Custom chain registry (bundled snapshot used if omitted).
    """

    _client_class = AsyncBlockpartyClient

    def __init__(
        self,
        credentials: list[ProviderCredential] | None = None,
        *,
        providers: ProviderSet | None = None,
        http_backend: Literal["aiohttp", "httpx"] = "aiohttp",
        cache_ttl: int = 30,
        registry: ChainRegistry | None = None,
    ) -> None:
        super().__init__(
            credentials,
            providers=providers,
            http_backend=http_backend,
            cache_ttl=cache_ttl,
            registry=registry,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close all cached client sessions."""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()

    async def __aenter__(self) -> AsyncBlockpartyPool:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # API endpoints — delegate to per-chain client
    # ------------------------------------------------------------------

    async def get_internal_transactions(
        self,
        chain_id: int,
        address: str,
        start_block: int = 0,
        end_block: int | None = None,
        page: int = 1,
        limit: int = 10,
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[InternalTransaction]:
        """Fetch internal transactions with provider fallback."""
        return await self._get_client(chain_id).get_internal_transactions(
            address=address,
            start_block=start_block,
            end_block=end_block,
            page=page,
            limit=limit,
            sort=sort,
            force_refresh=force_refresh,
        )

    async def get_normal_transactions(
        self,
        chain_id: int,
        address: str,
        start_block: int = 0,
        end_block: int | None = None,
        page: int = 1,
        limit: int = 10,
        sort: Literal["asc", "desc"] = "asc",
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[NormalTransaction]:
        """Fetch normal transactions with provider fallback."""
        return await self._get_client(chain_id).get_normal_transactions(
            address=address,
            start_block=start_block,
            end_block=end_block,
            page=page,
            limit=limit,
            sort=sort,
            force_refresh=force_refresh,
        )

    async def get_balance(
        self,
        chain_id: int,
        address: str | list[str],
        tag: str = "latest",
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Fetch native token balance with provider fallback."""
        return await self._get_client(chain_id).get_balance(
            address=address,
            tag=tag,
            force_refresh=force_refresh,
        )

    async def get_contract_abi(
        self,
        chain_id: int,
        address: str,
        *,
        force_refresh: bool = False,
    ) -> ScalarResponse:
        """Fetch contract ABI with provider fallback."""
        return await self._get_client(chain_id).get_contract_abi(
            address=address,
            force_refresh=force_refresh,
        )

    async def get_contract_source_code(
        self,
        chain_id: int,
        address: str,
        *,
        force_refresh: bool = False,
    ) -> ExplorerResponse[ContractSourceCode]:
        """Fetch contract source code with provider fallback."""
        return await self._get_client(chain_id).get_contract_source_code(
            address=address,
            force_refresh=force_refresh,
        )

    async def get_eth_price(
        self,
        chain_id: int,
        *,
        force_refresh: bool = False,
    ) -> ObjectResponse[EthPrice]:
        """Fetch native token price with provider fallback."""
        return await self._get_client(chain_id).get_eth_price(
            force_refresh=force_refresh,
        )

    async def get_gas_oracle(
        self,
        chain_id: int,
        *,
        force_refresh: bool = False,
    ) -> ObjectResponse[GasOracle]:
        """Fetch gas oracle with provider fallback."""
        return await self._get_client(chain_id).get_gas_oracle(
            force_refresh=force_refresh,
        )

    async def get_logs(
        self,
        chain_id: int,
        address: str | None = None,
        from_block: int = 0,
        to_block: int | None = None,
        topic0: str | None = None,
        page: int = 1,
        limit: int = 1000,
        *,
        force_refresh: bool = False,
        **kwargs: Any,
    ) -> ExplorerResponse[EventLog]:
        """Fetch event logs with provider fallback."""
        return await self._get_client(chain_id).get_logs(
            address=address,
            from_block=from_block,
            to_block=to_block,
            topic0=topic0,
            page=page,
            limit=limit,
            force_refresh=force_refresh,
            **kwargs,
        )
