"""Tests for blockparty.ratelimit — budget, registry, tier helpers."""

from __future__ import annotations

import pytest

from blockparty.ratelimit.budget import RateLimitBudget
from blockparty.ratelimit.registry import RateLimitRegistry
from blockparty.ratelimit.tiers import CustomRateLimit, EtherscanTier, get_rpd, get_rps


class TestGetRps:
    def test_none_returns_conservative_default(self):
        assert get_rps(None) == 5

    def test_from_tier_enum(self):
        assert get_rps(EtherscanTier.STANDARD) == 10

    def test_from_custom(self):
        assert get_rps(CustomRateLimit(rps=42, rpd=100_000)) == 42

    def test_get_rpd_from_tier(self):
        assert get_rpd(EtherscanTier.FREE) == 100_000


class TestRateLimitBudget:
    def test_initial_rps(self):
        b = RateLimitBudget(10)
        assert b.rps == 10.0

    def test_acquire_sync(self):
        b = RateLimitBudget(100)
        b.acquire_sync()  # Should not block with 100 tokens

    @pytest.mark.asyncio
    async def test_acquire_async(self):
        b = RateLimitBudget(100)
        await b.acquire()

    def test_update_from_headers(self):
        b = RateLimitBudget(5)
        b.update_from_headers(
            {
                "X-Ratelimit-Limit": "600",
                "X-Ratelimit-Remaining": "300",
                "X-Ratelimit-Reset": "60000",
            }
        )
        assert b.rps == 10.0  # 600 / 60

    def test_update_from_headers_ignores_missing(self):
        b = RateLimitBudget(5)
        b.update_from_headers({})
        assert b.rps == 5.0

    def test_update_from_headers_ignores_invalid(self):
        b = RateLimitBudget(5)
        b.update_from_headers(
            {
                "X-Ratelimit-Limit": "abc",
                "X-Ratelimit-Remaining": "1",
                "X-Ratelimit-Reset": "1000",
            }
        )
        assert b.rps == 5.0


class TestRateLimitRegistry:
    def test_same_key_returns_same_budget(self):
        reg = RateLimitRegistry()
        b1 = reg.get_or_create("etherscan", "KEY", EtherscanTier.STANDARD)
        b2 = reg.get_or_create("etherscan", "KEY", EtherscanTier.FREE)  # tier ignored
        assert b1 is b2

    def test_different_keys_return_different_budgets(self):
        reg = RateLimitRegistry()
        b1 = reg.get_or_create("etherscan", "KEY1")
        b2 = reg.get_or_create("etherscan", "KEY2")
        assert b1 is not b2

    def test_different_providers_return_different_budgets(self):
        reg = RateLimitRegistry()
        b1 = reg.get_or_create("etherscan", "KEY")
        b2 = reg.get_or_create("routescan", "KEY")
        assert b1 is not b2

    def test_none_key_is_valid(self):
        reg = RateLimitRegistry()
        b1 = reg.get_or_create("blockscout", None)
        b2 = reg.get_or_create("blockscout", None)
        assert b1 is b2
