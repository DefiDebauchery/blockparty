"""Connection pool with credential-ordered fallback."""

from blockparty.pool._base import ProviderCredential, ProviderSet, ResolvedProvider

# AsyncBlockpartyPool and SyncBlockpartyPool are imported lazily to avoid
# circular imports (they depend on the client modules, which depend on
# pool._base).

__all__ = [
    "AsyncBlockpartyPool",
    "ProviderCredential",
    "ProviderSet",
    "ResolvedProvider",
    "SyncBlockpartyPool",
]


def __getattr__(name: str):
    if name == "AsyncBlockpartyPool":
        from blockparty.pool.async_pool import AsyncBlockpartyPool

        return AsyncBlockpartyPool
    if name == "SyncBlockpartyPool":
        from blockparty.pool.sync_pool import SyncBlockpartyPool

        return SyncBlockpartyPool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
