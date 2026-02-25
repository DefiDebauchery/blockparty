"""Exception hierarchy for blockparty.

All exceptions inherit from :class:`BlockpartyError`, making it easy to catch
any library-level error with a single ``except`` clause.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from blockparty._types import ExplorerType


class BlockpartyError(Exception):
    """Base exception for all blockparty errors."""


# ---------------------------------------------------------------------------
# Configuration errors — raised before any HTTP request is made
# ---------------------------------------------------------------------------


class ConfigurationError(BlockpartyError):
    """Missing or invalid configuration.

    Examples: Blockscout selected but no hostname provided and chain
    is not in the registry, or conflicting options.
    """


class ChainNotFoundError(BlockpartyError):
    """The requested chain ID was not found in the registry."""

    def __init__(self, chain_id: int) -> None:
        self.chain_id = chain_id
        super().__init__(f"Chain {chain_id} not found in registry")


class ExplorerNotFoundError(BlockpartyError):
    """No explorer of the requested type supports this chain."""

    def __init__(self, chain_id: int, explorer_type: ExplorerType | None = None) -> None:
        self.chain_id = chain_id
        self.explorer_type = explorer_type
        if explorer_type:
            msg = f"No {explorer_type} explorer found for chain {chain_id}"
        else:
            msg = f"No explorer found for chain {chain_id}"
        super().__init__(msg)


# ---------------------------------------------------------------------------
# API errors — raised after an HTTP response is received
# ---------------------------------------------------------------------------


class ExplorerAPIError(BlockpartyError):
    """The explorer API returned an error response (``status=0`` or unexpected shape).

    Attributes:
        api_message: The ``message`` field from the response.
        api_result: The ``result`` field from the response, if present.
    """

    def __init__(self, message: str, result: str | None = None) -> None:
        self.api_message = message
        self.api_result = result
        super().__init__(f"Explorer API error: {message}")


class InvalidAPIKeyError(ExplorerAPIError):
    """API key is missing, invalid, or lacks the required permissions."""


class RateLimitError(ExplorerAPIError):
    """Rate limit exceeded for this provider/credential pair."""


class PremiumEndpointError(ExplorerAPIError):
    """The requested endpoint requires a premium/paid API subscription.

    Etherscan returns this for API Pro endpoints, e.g.:
    ``"Sorry, it looks like you are trying to access an API Pro endpoint.
    Contact us to upgrade to API Pro."``
    """


class ChainNotSupportedError(ExplorerAPIError):
    """The current API plan does not support this chain.

    Etherscan's free tier restricts certain chains (e.g., Base, Optimism,
    BSC, Avalanche and their testnets), returning:
    ``"Free API access is not supported for this chain. Please upgrade
    your api plan for full chain coverage."``

    This is distinct from :class:`PremiumEndpointError` — the *chain* is
    restricted, not the endpoint.  Upgrading the Etherscan plan resolves it,
    but falling back to Routescan/Blockscout is also a valid strategy.
    """


class InvalidAddressError(ExplorerAPIError):
    """The address format is invalid.

    This is a non-retryable, non-fallback error — the request itself is wrong.
    """


# ---------------------------------------------------------------------------
# Pool errors — raised when all providers in a pool have been exhausted
# ---------------------------------------------------------------------------


class PoolExhaustedError(BlockpartyError):
    """All providers in the pool failed for a given request.

    Attributes:
        provider_errors: Ordered list of ``(explorer_type, exception)`` pairs
            for each provider that was attempted.
    """

    def __init__(self, errors: list[tuple[ExplorerType, Exception]]) -> None:
        self.provider_errors = errors
        summary = "; ".join(f"{provider}: {err}" for provider, err in errors)
        super().__init__(f"All providers failed: {summary}")
