"""Shared client logic: base class, response parsing, and fallback helpers.

Both :class:`AsyncBlockpartyClient` and :class:`SyncBlockpartyClient` inherit
from :class:`BlockpartyClientBase` (properties, URL builders, init logic) and
use the parse helpers to convert raw API dicts into typed Pydantic models.
"""

from __future__ import annotations

import warnings
from typing import Any, TypeVar

from pydantic import BaseModel

from blockparty._types import ExplorerType
from blockparty.backends._base import ExplorerBackend
from blockparty.client._middleware import ResponseCache
from blockparty.exceptions import ExplorerNotFoundError
from blockparty.models.responses import (
    ExplorerResponse,
    InternalTransaction,
    ObjectResponse,
    ScalarResponse,
)
from blockparty.pool._base import (
    ProviderSet,
    ResolvedProvider,
    is_auth_error,
)
from blockparty.ratelimit.tiers import TierSpec
from blockparty.registry.chain_registry import ChainRegistry
from blockparty.urls.builder import ExplorerURLs
from blockparty.warnings import AuthFallbackWarning, FallbackWarning

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# Base client class
# ---------------------------------------------------------------------------


class BlockpartyClientBase:
    """Shared base for async and sync clients.

    Handles provider resolution, caching setup, URL building, and all
    non-async properties.  Subclasses add transport creation, ``_execute()``,
    lifecycle methods, and the ~40 typed endpoint methods.
    """

    def __init__(
        self,
        chain_id: int,
        *,
        providers: ProviderSet | None = None,
        explorer_type: ExplorerType | None = None,
        api_key: str | None = None,
        tier: TierSpec = None,
        http_backend: str = "",
        transport: Any = None,
        cache_ttl: int = 30,
        registry: ChainRegistry | None = None,
    ) -> None:
        self._chain_id = chain_id
        self._http_backend = http_backend
        self._user_transport = transport
        self._registry = registry or ChainRegistry.load()
        self._cache = ResponseCache(ttl=cache_ttl)

        # Build or use the provided ProviderSet.
        if providers is not None:
            self._providers = providers
        else:
            self._providers = ProviderSet.from_single(
                explorer_type,
                api_key,
                tier,
                chain_id,
                self._registry,
            )

        # Resolve providers for this chain (ordered, filtered).
        self._resolved: list[ResolvedProvider] = self._providers.resolve_for_chain(
            chain_id,
            self._registry,
        )
        if not self._resolved:
            raise ExplorerNotFoundError(chain_id)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def chain_id(self) -> int:
        """The EVM chain ID this client is configured for."""
        return self._chain_id

    @property
    def explorer_type(self) -> ExplorerType:
        """The primary (first) explorer type for this client."""
        return self._resolved[0].explorer_info.type

    @property
    def urls(self) -> ExplorerURLs:
        """Get a URL builder for this client's primary (preferred) explorer."""
        info = self._resolved[0].explorer_info
        entry = self._registry.get(self._chain_id)
        return ExplorerURLs(
            explorer_type=info.type,
            frontend_url=info.frontend_url,
            frontend_url_vanity=info.frontend_url_vanity,
            chain_id=self._chain_id,
            is_testnet=entry.is_testnet,
        )

    def urls_for(self, explorer_type: ExplorerType | None) -> ExplorerURLs:
        """Get a URL builder for a specific explorer type.

        Useful after a fallback — pass ``response.provider`` to get URLs
        matching the explorer that actually served the response::

            resp = client.get_internal_transactions(address="0x...")
            urls = client.urls_for(resp.provider)
            print(urls.tx(resp.result[0].hash))

        Falls back to the primary explorer if *explorer_type* is ``None``
        or not found among the resolved providers.
        """
        if explorer_type is not None:
            for rp in self._resolved:
                if rp.credential.type == explorer_type:
                    entry = self._registry.get(self._chain_id)
                    return ExplorerURLs(
                        explorer_type=rp.explorer_info.type,
                        frontend_url=rp.explorer_info.frontend_url,
                        frontend_url_vanity=rp.explorer_info.frontend_url_vanity,
                        chain_id=self._chain_id,
                        is_testnet=entry.is_testnet,
                    )
        return self.urls


# ---------------------------------------------------------------------------
# Fallback warning helper
# ---------------------------------------------------------------------------


def emit_fallback_warning(
    rp: ResolvedProvider,
    chain_id: int,
    exc: Exception,
) -> None:
    """Emit a :class:`FallbackWarning` or :class:`AuthFallbackWarning`."""
    warning_cls = AuthFallbackWarning if is_auth_error(exc) else FallbackWarning
    warnings.warn(
        f"{rp.credential.type} failed for chain {chain_id}: {exc}",
        warning_cls,
        stacklevel=4,
    )


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def _check_error(data: dict[str, Any], backend: ExplorerBackend) -> None:
    """Raise an exception if the API response indicates an error."""
    error = backend.parse_error(data)
    if error is not None:
        raise error


def _coerce_result_list(data: dict[str, Any]) -> list[Any]:
    """Extract result as a list, treating string results as empty."""
    raw = data.get("result", [])
    if isinstance(raw, str):
        return []
    return raw


def parse_internal_tx_response(
    data: dict[str, Any],
    backend: ExplorerBackend,
) -> ExplorerResponse[InternalTransaction]:
    """Parse a raw JSON response into a typed ExplorerResponse.

    Handles backend-specific normalization before Pydantic validation.
    """
    _check_error(data, backend)

    raw_results = _coerce_result_list(data)
    normalized_results = [backend.normalize_internal_tx(item) for item in raw_results]

    return ExplorerResponse[InternalTransaction].model_validate(
        {
            "status": data.get("status"),
            "message": data.get("message", "OK"),
            "result": normalized_results,
        }
    )


def parse_list_response(
    data: dict[str, Any],
    backend: ExplorerBackend,
    model: type[T],
) -> ExplorerResponse[T]:
    """Parse a raw JSON response into a typed ExplorerResponse with list result."""
    _check_error(data, backend)

    raw_results = _coerce_result_list(data)

    return ExplorerResponse[model].model_validate(
        {
            "status": data.get("status"),
            "message": data.get("message", "OK"),
            "result": raw_results,
        }
    )


def parse_scalar_response(
    data: dict[str, Any],
    backend: ExplorerBackend,
) -> ScalarResponse:
    """Parse a raw JSON response whose result is a scalar string."""
    _check_error(data, backend)

    return ScalarResponse.model_validate(
        {
            "status": data.get("status"),
            "message": data.get("message", "OK"),
            "result": str(data.get("result", "")),
        }
    )


def parse_object_response(
    data: dict[str, Any],
    backend: ExplorerBackend,
    model: type[T],
) -> ObjectResponse[T]:
    """Parse a raw JSON response whose result is a single object."""
    _check_error(data, backend)

    return ObjectResponse[model].model_validate(
        {
            "status": data.get("status"),
            "message": data.get("message", "OK"),
            "result": data.get("result", {}),
        }
    )
