"""Abstract base for explorer backends.

Provides two layers:

- :class:`ExplorerBackend` — a :class:`~typing.Protocol` for structural
  subtyping.  Consumers can type-hint against this without requiring
  inheritance.
- :class:`ExplorerBackendBase` — a concrete abstract base class that
  implements the shared logic (param building, error parsing) so that
  the individual backends (Etherscan, Routescan, Blockscout) only need
  to define ``name`` and any provider-specific overrides.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from blockparty._types import ExplorerType
from blockparty.backends._errors import classify_error
from blockparty.exceptions import ExplorerAPIError


@runtime_checkable
class ExplorerBackend(Protocol):
    """Protocol defining the interface for an explorer backend.

    Backends are stateless — they receive all required context (API URL,
    chain ID, API key) as arguments rather than storing them internally.
    This allows a single backend instance to be shared across multiple
    chains and clients.
    """

    @property
    def name(self) -> ExplorerType: ...

    def build_request_params(
        self,
        *,
        module: str,
        action: str,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> dict[str, str]: ...

    def normalize_internal_tx(self, raw: dict[str, Any]) -> dict[str, Any]: ...

    def parse_error(self, response_data: dict[str, Any]) -> ExplorerAPIError | None: ...


class ExplorerBackendBase(ABC):
    """Concrete base class implementing shared backend logic.

    Subclasses must define :attr:`name`.  Override
    :meth:`normalize_internal_tx` and :meth:`parse_error` only when the
    provider diverges from the Etherscan-standard pattern.
    """

    @property
    @abstractmethod
    def name(self) -> ExplorerType: ...

    # ------------------------------------------------------------------
    # Shared: param building
    # ------------------------------------------------------------------

    def build_request_params(
        self,
        *,
        module: str,
        action: str,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> dict[str, str]:
        """Build the query parameter dict for an API request.

        Assembles ``module``, ``action``, optional ``apikey``, and any
        endpoint-specific params into a flat dict of string key-value pairs.
        ``None`` values in *kwargs* are silently dropped.
        """
        params: dict[str, str] = {
            "module": module,
            "action": action,
        }
        if api_key is not None:
            params["apikey"] = api_key

        for key, value in kwargs.items():
            if value is not None:
                params[key] = str(value)

        return params

    # ------------------------------------------------------------------
    # Shared: normalization (passthrough by default)
    # ------------------------------------------------------------------

    def normalize_internal_tx(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize a raw internal transaction dict.

        The default implementation is a passthrough — Etherscan and Routescan
        already use the canonical field names.  Blockscout overrides this to
        remap ``transactionHash`` -> ``hash``.
        """
        return raw

    # ------------------------------------------------------------------
    # Shared: error parsing
    # ------------------------------------------------------------------

    def parse_error(self, response_data: dict[str, Any]) -> ExplorerAPIError | None:
        """Inspect a parsed JSON response for error conditions.

        The Etherscan/Routescan convention is ``status="0"`` for errors,
        with details in ``message`` and ``result``.  Returns a typed
        exception if an error is detected, or ``None`` if the response
        is successful.
        """
        status = response_data.get("status")
        if status != "0":
            return None

        message = response_data.get("message", "")
        result = response_data.get("result", "")
        result_str = result if isinstance(result, str) else None

        return classify_error(message, result_str)
