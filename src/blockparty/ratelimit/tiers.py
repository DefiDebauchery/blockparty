"""Provider rate limit tier definitions.

Each explorer provider has distinct pricing tiers with different rate limits.
These enums encode the known tiers so consumers can declare their plan and
get correct token bucket configuration automatically.

For enterprise or non-standard limits, :class:`CustomRateLimit` provides
an escape hatch.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EtherscanTier(Enum):
    """Etherscan API plan tiers with their rate limits."""

    FREE = "free"  # 3 rps / 100K rpd
    LITE = "lite"  # 5 rps / 100K rpd
    STANDARD = "standard"  # 10 rps / 200K rpd
    ADVANCED = "advanced"  # 20 rps / 500K rpd
    PROFESSIONAL = "pro"  # 30 rps / 1M rpd

    @property
    def rps(self) -> int:
        """Requests per second for this tier."""
        return _ETHERSCAN_LIMITS[self][0]

    @property
    def rpd(self) -> int:
        """Requests per day for this tier."""
        return _ETHERSCAN_LIMITS[self][1]


_ETHERSCAN_LIMITS: dict[EtherscanTier, tuple[int, int]] = {
    EtherscanTier.FREE: (3, 100_000),
    EtherscanTier.LITE: (5, 100_000),
    EtherscanTier.STANDARD: (10, 200_000),
    EtherscanTier.ADVANCED: (20, 500_000),
    EtherscanTier.PROFESSIONAL: (30, 1_000_000),
}


class RoutescanTier(Enum):
    """Routescan API plan tiers with their rate limits."""

    ANONYMOUS = "anonymous"  # 2 rps / 10K rpd (no key)
    FREE = "free"  # 5 rps / 100K rpd
    STANDARD = "standard"  # 10 rps / 200K rpd
    ADVANCED = "advanced"  # 20 rps / 500K rpd
    PROFESSIONAL = "pro"  # 30 rps / 1M rpd
    PRO_PLUS = "pro_plus"  # 30 rps / 1.5M rpd

    @property
    def rps(self) -> int:
        """Requests per second for this tier."""
        return _ROUTESCAN_LIMITS[self][0]

    @property
    def rpd(self) -> int:
        """Requests per day for this tier."""
        return _ROUTESCAN_LIMITS[self][1]


_ROUTESCAN_LIMITS: dict[RoutescanTier, tuple[int, int]] = {
    RoutescanTier.ANONYMOUS: (2, 10_000),
    RoutescanTier.FREE: (5, 100_000),
    RoutescanTier.STANDARD: (10, 200_000),
    RoutescanTier.ADVANCED: (20, 500_000),
    RoutescanTier.PROFESSIONAL: (30, 1_000_000),
    RoutescanTier.PRO_PLUS: (30, 1_500_000),
}


class BlockscoutTier(Enum):
    """Blockscout API access tiers.

    Blockscout dynamically communicates rate limits via response headers
    (``X-Ratelimit-*``), so these tiers serve only as *initial* bucket
    configuration.  The rate limit middleware adapts from headers on every
    response.
    """

    ANONYMOUS = "anonymous"  # ~5 rps
    KEYED = "keyed"  # ~10 rps

    @property
    def rps(self) -> int:
        """Requests per second for this tier."""
        return _BLOCKSCOUT_LIMITS[self][0]

    @property
    def rpd(self) -> int:
        """Requests per day for this tier."""
        return _BLOCKSCOUT_LIMITS[self][1]


_BLOCKSCOUT_LIMITS: dict[BlockscoutTier, tuple[int, int]] = {
    BlockscoutTier.ANONYMOUS: (5, 100_000),
    BlockscoutTier.KEYED: (10, 200_000),
}


@dataclass(frozen=True)
class CustomRateLimit:
    """Escape hatch for enterprise plans or non-standard limits.

    Usage::

        client = AsyncBlockpartyClient(
            chain_id=8453,
            explorer_type="etherscan",
            api_key="...",
            tier=CustomRateLimit(rps=50, rpd=2_000_000),
        )
    """

    rps: int
    rpd: int


# Type alias for any tier specification.
TierSpec = EtherscanTier | RoutescanTier | BlockscoutTier | CustomRateLimit | None


def get_rps(tier: TierSpec) -> int:
    """Extract requests-per-second from any tier specification."""
    if tier is None:
        return 5  # conservative default
    if isinstance(tier, CustomRateLimit):
        return tier.rps
    return tier.rps  # all enums have .rps


def get_rpd(tier: TierSpec) -> int:
    """Extract requests-per-day from any tier specification."""
    if tier is None:
        return 100_000  # conservative default
    if isinstance(tier, CustomRateLimit):
        return tier.rpd
    return tier.rpd  # all enums have .rpd
