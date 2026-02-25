"""Tests for blockparty.client._middleware — cache and retry config."""

from __future__ import annotations

from blockparty.client._middleware import ResponseCache, RetryConfig


class TestResponseCache:
    def test_set_and_get(self):
        cache = ResponseCache(ttl=60)
        cache.set("key1", {"data": 42})
        assert cache.get("key1") == {"data": 42}

    def test_miss_returns_none(self):
        assert ResponseCache(ttl=60).get("nonexistent") is None

    def test_ttl_zero_disables(self):
        cache = ResponseCache(ttl=0)
        cache.set("key1", {"data": 42})
        assert cache.get("key1") is None

    def test_key_is_deterministic_regardless_of_order(self):
        k1 = ResponseCache.make_key({"a": "1", "b": "2"})
        k2 = ResponseCache.make_key({"b": "2", "a": "1"})
        assert k1 == k2

    def test_different_params_produce_different_keys(self):
        k1 = ResponseCache.make_key({"a": "1"})
        k2 = ResponseCache.make_key({"a": "2"})
        assert k1 != k2


class TestRetryConfig:
    def test_delay_increases_with_attempts(self):
        rc = RetryConfig(jitter_factor=0)
        assert rc.delay(0) < rc.delay(1) < rc.delay(2)

    def test_delay_respects_cap(self):
        rc = RetryConfig(max_backoff=5.0, jitter_factor=0)
        assert rc.delay(100) <= 5.0

    def test_retryable_statuses(self):
        rc = RetryConfig()
        assert rc.should_retry_status(429)
        assert rc.should_retry_status(503)
        assert not rc.should_retry_status(200)
        assert not rc.should_retry_status(400)
