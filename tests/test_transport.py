"""Tests for blockparty.client._transport."""

from __future__ import annotations

import pytest

from blockparty.client._transport import (
    TransportConnectionError,
    TransportError,
    TransportHTTPError,
    TransportTimeout,
    create_async_transport,
    create_sync_transport,
    wrap_async_transport,
    wrap_sync_transport,
)


class TestTransportExceptions:
    def test_hierarchy(self):
        assert issubclass(TransportTimeout, TransportError)
        assert issubclass(TransportConnectionError, TransportError)
        assert issubclass(TransportHTTPError, TransportError)

    def test_http_error_has_status_code(self):
        err = TransportHTTPError(429, "Too Many Requests")
        assert err.status_code == 429


class TestWrapTransport:
    def test_unknown_async_raises(self):
        with pytest.raises(TypeError, match="Unsupported async"):
            wrap_async_transport("not a session")

    def test_unknown_sync_raises(self):
        with pytest.raises(TypeError, match="Unsupported sync"):
            wrap_sync_transport("not a session")

    def test_protocol_conforming_async_passthrough(self, mock_async_transport):
        assert wrap_async_transport(mock_async_transport) is mock_async_transport

    def test_protocol_conforming_sync_passthrough(self, mock_sync_transport):
        assert wrap_sync_transport(mock_sync_transport) is mock_sync_transport


class TestCreateTransport:
    @pytest.mark.asyncio
    async def test_create_async_aiohttp(self):
        transport, owns = create_async_transport("aiohttp")
        assert owns is True
        await transport.close()

    def test_create_sync_requests(self):
        transport, owns = create_sync_transport("requests")
        assert owns is True
        transport.close()

    def test_invalid_async_backend_raises(self):
        with pytest.raises(ValueError, match="Unknown async"):
            create_async_transport("nonexistent")

    def test_invalid_sync_backend_raises(self):
        with pytest.raises(ValueError, match="Unknown sync"):
            create_sync_transport("nonexistent")
