"""Shared pool logic: credentials, provider sets, fallback, and pool base class.

:class:`ProviderCredential` defines a single provider + key + tier.
:class:`ProviderSet` holds an ordered list of credentials with a shared
:class:`~blockparty.ratelimit.registry.RateLimitRegistry`, resolving which
providers are eligible for a given chain and managing rate limit budgets.
:class:`BlockpartyPoolBase` provides shared init, URL building, and client
caching for async and sync pool subclasses.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from blockparty._types import EXPLORER_PRIORITY, ExplorerType
from blockparty.backends import BlockscoutBackend, EtherscanBackend, ExplorerBackend, RoutescanBackend
from blockparty.exceptions import (
    ExplorerNotFoundError,
    InvalidAddressError,
    InvalidAPIKeyError,
    PremiumEndpointError,
)
from blockparty.models.registry import ExplorerInfo
from blockparty.ratelimit.budget import RateLimitBudget
from blockparty.ratelimit.registry import RateLimitRegistry
from blockparty.ratelimit.tiers import TierSpec
from blockparty.registry.chain_registry import ChainRegistry
from blockparty.urls.builder import ExplorerURLs

# ---------------------------------------------------------------------------
# Backend singletons (stateless — safe to share)
# ---------------------------------------------------------------------------

BACKENDS: dict[ExplorerType, ExplorerBackend] = {
    "etherscan": EtherscanBackend(),
    "routescan": RoutescanBackend(),
    "blockscout": BlockscoutBackend(),
}


# ---------------------------------------------------------------------------
# Credential model
# ---------------------------------------------------------------------------


class ProviderCredential(BaseModel):
    """Defines a provider and its authentication / rate limit configuration.

    The order of credentials in a :class:`ProviderSet` determines the
    fallback order — first credential is tried first.

    Attributes:
        type: The explorer provider.
        api_key: Optional API key.  Required for Etherscan, optional for others.
        tier: Rate limit tier for bucket configuration.
        chain_ids: If set, this credential is only used for these chain IDs.
            ``None`` (default) means the credential applies to all chains.
    """

    type: ExplorerType
    api_key: str | None = None
    tier: TierSpec = None
    chain_ids: frozenset[int] | None = None

    def matches_chain(self, chain_id: int) -> bool:
        """Check if this credential is eligible for the given chain."""
        return self.chain_ids is None or chain_id in self.chain_ids


# ---------------------------------------------------------------------------
# Resolved provider tuple
# ---------------------------------------------------------------------------


class ResolvedProvider:
    """A single eligible provider for a specific chain, ready to use.

    Bundles the credential, explorer info, backend, and rate limit budget.
    """

    __slots__ = ("credential", "explorer_info", "backend", "budget")

    def __init__(
        self,
        credential: ProviderCredential,
        explorer_info: ExplorerInfo,
        backend: ExplorerBackend,
        budget: RateLimitBudget,
    ) -> None:
        self.credential = credential
        self.explorer_info = explorer_info
        self.backend = backend
        self.budget = budget


# ---------------------------------------------------------------------------
# Provider set
# ---------------------------------------------------------------------------


class ProviderSet:
    """Ordered credential store with shared rate limiting.

    Holds an ordered list of :class:`ProviderCredential` and a
    :class:`~blockparty.ratelimit.registry.RateLimitRegistry`.  Multiple
    clients sharing one ``ProviderSet`` automatically share rate limit
    budgets for identical ``(provider, api_key)`` pairs.

    Example::

        providers = ProviderSet([
            ProviderCredential(type="etherscan", api_key="KEY", tier=EtherscanTier.STANDARD),
            ProviderCredential(type="routescan", tier=RoutescanTier.ANONYMOUS),
            ProviderCredential(type="blockscout"),
        ])

        client_a = AsyncBlockpartyClient(chain_id=8453, providers=providers)
        client_b = AsyncBlockpartyClient(chain_id=42161, providers=providers)
        # Both share rate limit budgets via the same ProviderSet.
    """

    __slots__ = ("_credentials", "_rate_limit_registry")

    def __init__(
        self,
        credentials: list[ProviderCredential],
        *,
        rate_limit_registry: RateLimitRegistry | None = None,
    ) -> None:
        self._credentials = credentials
        self._rate_limit_registry = rate_limit_registry or RateLimitRegistry()

    @property
    def rate_limit_registry(self) -> RateLimitRegistry:
        """The shared rate limit registry."""
        return self._rate_limit_registry

    def resolve_for_chain(
        self,
        chain_id: int,
        registry: ChainRegistry,
    ) -> list[ResolvedProvider]:
        """Return eligible providers for a chain, in priority order.

        Filters credentials by chain_id match and explorer availability.
        Each returned :class:`ResolvedProvider` includes the credential,
        explorer info, backend singleton, and rate limit budget.

        Args:
            chain_id: The EVM chain ID.
            registry: The chain registry for explorer lookup.

        Returns:
            An ordered list of resolved providers.

        Raises:
            ChainNotFoundError: If the chain is not in the registry.
        """
        entry = registry.get(chain_id)
        explorers_by_type: dict[ExplorerType, ExplorerInfo] = {e.type: e for e in entry.explorers}

        results: list[ResolvedProvider] = []
        for cred in self._credentials:
            if not cred.matches_chain(chain_id):
                continue
            if cred.type not in explorers_by_type:
                continue
            budget = self._rate_limit_registry.get_or_create(
                cred.type,
                cred.api_key,
                cred.tier,
            )
            results.append(
                ResolvedProvider(
                    credential=cred,
                    explorer_info=explorers_by_type[cred.type],
                    backend=BACKENDS[cred.type],
                    budget=budget,
                )
            )
        return results

    @classmethod
    def from_single(
        cls,
        explorer_type: ExplorerType | None,
        api_key: str | None,
        tier: TierSpec,
        chain_id: int,
        registry: ChainRegistry,
    ) -> ProviderSet:
        """Create a single-credential ProviderSet for backward compatibility.

        Used when a client is created with explicit ``explorer_type`` / ``api_key``
        instead of a ``ProviderSet``.

        Resolution logic:
            1. If ``explorer_type`` is given, use that.
            2. If ``api_key`` is provided (without type), prefer Etherscan.
            3. Otherwise, use priority order: Etherscan > Routescan > Blockscout.
        """
        if explorer_type is not None:
            return cls([ProviderCredential(type=explorer_type, api_key=api_key, tier=tier)])

        # Resolve from chain registry.
        entry = registry.get(chain_id)
        available_types = {e.type for e in entry.explorers}

        if api_key and "etherscan" in available_types:
            return cls([ProviderCredential(type="etherscan", api_key=api_key, tier=tier)])

        # Default priority order.
        for ptype in EXPLORER_PRIORITY:
            if ptype in available_types:
                return cls([ProviderCredential(type=ptype, api_key=api_key, tier=tier)])

        raise ExplorerNotFoundError(chain_id)

    def __len__(self) -> int:
        return len(self._credentials)

    def __repr__(self) -> str:
        types = [c.type for c in self._credentials]
        return f"ProviderSet({types})"


# ---------------------------------------------------------------------------
# Fallback classification
# ---------------------------------------------------------------------------

# Errors that indicate a problem with the *input* — no provider can help.
_NON_FALLBACK_ERRORS: tuple[type[Exception], ...] = (
    InvalidAddressError,
    PremiumEndpointError,
)


def is_fallback_eligible(error: Exception) -> bool:
    """Determine whether an error should trigger a fallback to the next provider.

    Non-fallback errors (bad input, premium-only endpoints) are raised
    immediately.  Everything else — connection errors, rate limits, 5xx,
    auth failures — triggers a fallback with an appropriate warning.

    Returns:
        ``True`` if the pool should try the next provider.
    """
    if isinstance(error, _NON_FALLBACK_ERRORS):
        return False
    return True


def is_auth_error(error: Exception) -> bool:
    """Check if an error is an authentication issue (for warning classification)."""
    return isinstance(error, InvalidAPIKeyError)


# ---------------------------------------------------------------------------
# Pool base class
# ---------------------------------------------------------------------------


class BlockpartyPoolBase:
    """Shared base for async and sync connection pools.

    Handles provider/credential resolution, client caching, and URL building.
    Subclasses add lifecycle methods (``close``, context managers) and typed
    endpoint methods that delegate to the cached clients.

    The ``_client_class`` class attribute must be set by subclasses to the
    concrete client type (``AsyncBlockpartyClient`` or ``SyncBlockpartyClient``).
    """

    _client_class: type[Any]  # Set by subclasses.

    def __init__(
        self,
        credentials: list[ProviderCredential] | None = None,
        *,
        providers: ProviderSet | None = None,
        http_backend: str = "",
        cache_ttl: int = 30,
        registry: ChainRegistry | None = None,
    ) -> None:
        if providers is not None:
            self._providers = providers
        elif credentials is not None:
            self._providers = ProviderSet(credentials)
        else:
            raise ValueError("Either 'credentials' or 'providers' must be given.")

        self._http_backend = http_backend
        self._cache_ttl = cache_ttl
        self._registry = registry or ChainRegistry.load()
        self._clients: dict[int, Any] = {}

    def _get_client(self, chain_id: int) -> Any:
        """Get or create a cached client for this chain."""
        if chain_id not in self._clients:
            self._clients[chain_id] = self._client_class(
                chain_id=chain_id,
                providers=self._providers,
                http_backend=self._http_backend,
                cache_ttl=self._cache_ttl,
                registry=self._registry,
            )
        return self._clients[chain_id]

    def urls(self, chain_id: int) -> ExplorerURLs:
        """Get a URL builder for the preferred explorer on this chain."""
        return self._get_client(chain_id).urls

    def urls_for(self, chain_id: int, explorer_type: ExplorerType | None) -> ExplorerURLs:
        """Get a URL builder for the explorer that actually served a response.

        Usage::

            resp = pool.get_internal_transactions(chain_id=8453, address="0x...")
            urls = pool.urls_for(8453, resp.provider)
            print(urls.tx(resp.result[0].hash))
        """
        return self._get_client(chain_id).urls_for(explorer_type)
