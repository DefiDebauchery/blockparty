"""Tests for blockparty.exceptions — hierarchy and error formatting."""

from __future__ import annotations

from blockparty.exceptions import (
    BlockpartyError,
    ChainNotFoundError,
    ChainNotSupportedError,
    ExplorerAPIError,
    ExplorerNotFoundError,
    InvalidAddressError,
    InvalidAPIKeyError,
    PoolExhaustedError,
    PremiumEndpointError,
    RateLimitError,
)


class TestExceptionHierarchy:
    def test_all_inherit_from_base(self):
        for cls in [
            ChainNotFoundError,
            ExplorerNotFoundError,
            ExplorerAPIError,
            InvalidAPIKeyError,
            RateLimitError,
            PremiumEndpointError,
            InvalidAddressError,
            PoolExhaustedError,
            ChainNotSupportedError,
        ]:
            assert issubclass(cls, BlockpartyError)

    def test_api_error_subclasses(self):
        for cls in [
            InvalidAPIKeyError,
            RateLimitError,
            PremiumEndpointError,
            InvalidAddressError,
            ChainNotSupportedError,
        ]:
            assert issubclass(cls, ExplorerAPIError)

    def test_pool_exhausted_collects_errors(self):
        errors = [
            ("etherscan", RateLimitError("rate limited")),
            ("routescan", ExplorerAPIError("error")),
        ]
        err = PoolExhaustedError(errors)
        assert len(err.provider_errors) == 2
        assert "etherscan" in str(err)
