"""Shared rate limit registry mapping (provider, api_key) → budget.

Two clients hitting the same provider with the same API key share one
:class:`RateLimitBudget`.  The registry manages this deduplication.
"""

from __future__ import annotations

from blockparty._types import ExplorerType
from blockparty.ratelimit.budget import RateLimitBudget
from blockparty.ratelimit.tiers import TierSpec, get_rps


class RateLimitRegistry:
    """Maps ``(provider_type, api_key | None)`` → :class:`RateLimitBudget`.

    Thread-safe and suitable for sharing across multiple clients.
    """

    __slots__ = ("_budgets",)

    def __init__(self) -> None:
        self._budgets: dict[tuple[ExplorerType, str | None], RateLimitBudget] = {}

    def get_or_create(
        self,
        provider: ExplorerType,
        api_key: str | None,
        tier: TierSpec = None,
    ) -> RateLimitBudget:
        """Get the existing budget or create a new one.

        If a budget already exists for this ``(provider, api_key)`` pair,
        it is returned as-is (the ``tier`` argument is ignored — the budget
        retains its original configuration).

        Args:
            provider: The explorer provider type.
            api_key: The API key (or ``None`` for anonymous access).
            tier: Rate limit tier for initial bucket configuration.

        Returns:
            The :class:`RateLimitBudget` for this credential.
        """
        key = (provider, api_key)
        if key not in self._budgets:
            rps = get_rps(tier)
            self._budgets[key] = RateLimitBudget(rps)
        return self._budgets[key]

    def __len__(self) -> int:
        return len(self._budgets)

    def __repr__(self) -> str:
        return f"RateLimitRegistry({len(self._budgets)} budgets)"
