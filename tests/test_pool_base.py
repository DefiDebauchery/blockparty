"""Tests for blockparty.pool._base — ProviderSet, credentials, fallback."""

from __future__ import annotations

import pytest

from blockparty.exceptions import (
    ChainNotFoundError,
    ExplorerAPIError,
    InvalidAddressError,
    InvalidAPIKeyError,
    PremiumEndpointError,
    RateLimitError,
)
from blockparty.pool._base import (
    ProviderCredential,
    ProviderSet,
    is_auth_error,
    is_fallback_eligible,
)
from blockparty.ratelimit.tiers import EtherscanTier


class TestProviderCredential:
    def test_matches_all_chains_when_none(self):
        pc = ProviderCredential(type="etherscan")
        assert pc.matches_chain(1)
        assert pc.matches_chain(999999)

    def test_matches_only_specified_chains(self):
        pc = ProviderCredential(type="etherscan", chain_ids=frozenset({8453, 10}))
        assert pc.matches_chain(8453)
        assert not pc.matches_chain(1)


class TestProviderSet:
    def test_resolve_returns_all_matching(self, mock_registry):
        ps = ProviderSet([
            ProviderCredential(type="etherscan", api_key="K", tier=EtherscanTier.FREE),
            ProviderCredential(type="routescan"),
            ProviderCredential(type="blockscout"),
        ])
        resolved = ps.resolve_for_chain(1, mock_registry)
        assert len(resolved) == 3
        assert [r.credential.type for r in resolved] == ["etherscan", "routescan", "blockscout"]

    def test_resolve_filters_unavailable_explorers(self, mock_registry):
        """Chain 999 only has blockscout."""
        ps = ProviderSet([
            ProviderCredential(type="etherscan", api_key="K"),
            ProviderCredential(type="blockscout"),
        ])
        resolved = ps.resolve_for_chain(999, mock_registry)
        assert len(resolved) == 1
        assert resolved[0].credential.type == "blockscout"

    def test_resolve_filters_by_chain_ids(self, mock_registry):
        ps = ProviderSet([
            ProviderCredential(type="etherscan", api_key="PREMIUM", chain_ids=frozenset({8453})),
            ProviderCredential(type="etherscan", api_key="FREE"),
        ])
        assert len(ps.resolve_for_chain(8453, mock_registry)) == 2
        resolved_1 = ps.resolve_for_chain(1, mock_registry)
        assert len(resolved_1) == 1
        assert resolved_1[0].credential.api_key == "FREE"

    def test_shared_budgets_across_chains(self, mock_registry):
        ps = ProviderSet([
            ProviderCredential(type="etherscan", api_key="SHARED", tier=EtherscanTier.STANDARD),
        ])
        b1 = ps.resolve_for_chain(1, mock_registry)[0].budget
        b8453 = ps.resolve_for_chain(8453, mock_registry)[0].budget
        assert b1 is b8453

    def test_different_keys_get_different_budgets(self, mock_registry):
        ps = ProviderSet([
            ProviderCredential(type="etherscan", api_key="KEY_A"),
            ProviderCredential(type="etherscan", api_key="KEY_B"),
        ])
        resolved = ps.resolve_for_chain(1, mock_registry)
        assert resolved[0].budget is not resolved[1].budget

    def test_from_single_with_explicit_type(self, mock_registry):
        ps = ProviderSet.from_single("etherscan", "KEY", EtherscanTier.FREE, 1, mock_registry)
        assert len(ps) == 1

    def test_from_single_auto_resolves_with_key(self, mock_registry):
        ps = ProviderSet.from_single(None, "KEY", None, 1, mock_registry)
        resolved = ps.resolve_for_chain(1, mock_registry)
        assert resolved[0].credential.type == "etherscan"

    def test_from_single_auto_resolves_without_key(self, mock_registry):
        ps = ProviderSet.from_single(None, None, None, 1, mock_registry)
        resolved = ps.resolve_for_chain(1, mock_registry)
        assert resolved[0].credential.type == "etherscan"  # highest priority

    def test_unknown_chain_raises(self, mock_registry):
        ps = ProviderSet([ProviderCredential(type="etherscan")])
        with pytest.raises(ChainNotFoundError):
            ps.resolve_for_chain(999999, mock_registry)

    def test_supports_chain_true(self, mock_registry):
        ps = ProviderSet([
            ProviderCredential(type="etherscan", api_key="K"),
            ProviderCredential(type="blockscout"),
        ])
        assert ps.supports_chain(1, mock_registry) is True

    def test_supports_chain_false_not_in_registry(self, mock_registry):
        ps = ProviderSet([ProviderCredential(type="etherscan")])
        assert ps.supports_chain(999999, mock_registry) is False

    def test_supports_chain_false_no_matching_provider(self, mock_registry):
        """Chain 999 only has blockscout, but we only have etherscan."""
        ps = ProviderSet([ProviderCredential(type="etherscan", api_key="K")])
        assert ps.supports_chain(999, mock_registry) is False

    def test_supports_chain_respects_chain_ids(self, mock_registry):
        ps = ProviderSet([
            ProviderCredential(type="etherscan", api_key="K", chain_ids=frozenset({8453})),
        ])
        assert ps.supports_chain(8453, mock_registry) is True
        assert ps.supports_chain(1, mock_registry) is False


class TestFallbackClassification:
    @pytest.mark.parametrize("error, expected", [
        (RateLimitError("rate limited"), True),
        (InvalidAPIKeyError("bad key"), True),
        (ExplorerAPIError("unknown"), True),
        (ConnectionError("timeout"), True),
        (InvalidAddressError("bad addr"), False),
        (PremiumEndpointError("pro only"), False),
    ])
    def test_fallback_eligibility(self, error, expected):
        assert is_fallback_eligible(error) is expected

    def test_auth_error_detected(self):
        assert is_auth_error(InvalidAPIKeyError("bad key"))
        assert not is_auth_error(RateLimitError("rate limited"))
