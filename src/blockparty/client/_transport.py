"""HTTP transport layer — wraps aiohttp, requests, and httpx.

Provides a uniform interface for making HTTP requests regardless of the
underlying library.  Each transport implementation handles:

- Sending GET requests with query parameters
- Parsing JSON responses
- Mapping library-specific exceptions to blockparty errors
- Session lifecycle (close)

The transport is a dumb pipe: it takes a URL and params dict, returns JSON.
All business logic (param mapping, caching, rate limiting, error classification,
fallback) lives in the client's ``_execute()`` method.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TransportError(Exception):
    """Base exception for all transport-level errors."""


class TransportTimeout(TransportError):
    """The HTTP request timed out."""


class TransportConnectionError(TransportError):
    """Could not connect to the server."""


class TransportHTTPError(TransportError):
    """The server returned a non-2xx status code.

    Attributes:
        status_code: The HTTP status code.
    """

    def __init__(self, status_code: int, message: str = "") -> None:
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}" if message else f"HTTP {status_code}")


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class AsyncTransport(Protocol):
    """Async transport protocol."""

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str],
    ) -> dict[str, Any]: ...

    async def close(self) -> None: ...


@runtime_checkable
class SyncTransport(Protocol):
    """Sync transport protocol."""

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str],
    ) -> dict[str, Any]: ...

    def close(self) -> None: ...


# ---------------------------------------------------------------------------
# aiohttp transport
# ---------------------------------------------------------------------------


class AiohttpTransport:
    """Async transport using aiohttp."""

    __slots__ = ("_session",)

    def __init__(self, session: Any) -> None:
        self._session = session

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str],
    ) -> dict[str, Any]:
        import aiohttp

        try:
            async with self._session.request(method, url, params=params) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    raise TransportHTTPError(resp.status, text[:200])
                return await resp.json(content_type=None)
        except TransportError:
            raise
        except aiohttp.ServerTimeoutError as exc:
            raise TransportTimeout(str(exc)) from exc
        except (
            aiohttp.ClientConnectorError,
            aiohttp.ServerConnectionError,
            aiohttp.ServerDisconnectedError,
        ) as exc:
            raise TransportConnectionError(str(exc)) from exc
        except aiohttp.ClientError as exc:
            raise TransportError(str(exc)) from exc

    async def close(self) -> None:
        await self._session.close()


# ---------------------------------------------------------------------------
# requests transport
# ---------------------------------------------------------------------------


class RequestsTransport:
    """Sync transport using requests."""

    __slots__ = ("_session",)

    def __init__(self, session: Any) -> None:
        self._session = session

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str],
    ) -> dict[str, Any]:
        import requests

        try:
            resp = self._session.request(method, url, params=params)
            if resp.status_code >= 400:
                raise TransportHTTPError(resp.status_code, resp.text[:200])
            return resp.json()
        except TransportError:
            raise
        except requests.exceptions.Timeout as exc:
            raise TransportTimeout(str(exc)) from exc
        except requests.exceptions.ConnectionError as exc:
            raise TransportConnectionError(str(exc)) from exc
        except requests.exceptions.RequestException as exc:
            raise TransportError(str(exc)) from exc

    def close(self) -> None:
        self._session.close()


# ---------------------------------------------------------------------------
# httpx transports
# ---------------------------------------------------------------------------


class HttpxAsyncTransport:
    """Async transport using httpx."""

    __slots__ = ("_client",)

    def __init__(self, client: Any) -> None:
        self._client = client

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str],
    ) -> dict[str, Any]:
        import httpx

        try:
            resp = await self._client.request(method, url, params=params)
            if resp.status_code >= 400:
                raise TransportHTTPError(resp.status_code, resp.text[:200])
            return resp.json()
        except TransportError:
            raise
        except httpx.TimeoutException as exc:
            raise TransportTimeout(str(exc)) from exc
        except httpx.NetworkError as exc:
            raise TransportConnectionError(str(exc)) from exc
        except httpx.HTTPError as exc:
            raise TransportError(str(exc)) from exc

    async def close(self) -> None:
        await self._client.aclose()


class HttpxSyncTransport:
    """Sync transport using httpx."""

    __slots__ = ("_client",)

    def __init__(self, client: Any) -> None:
        self._client = client

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str],
    ) -> dict[str, Any]:
        import httpx

        try:
            resp = self._client.request(method, url, params=params)
            if resp.status_code >= 400:
                raise TransportHTTPError(resp.status_code, resp.text[:200])
            return resp.json()
        except TransportError:
            raise
        except httpx.TimeoutException as exc:
            raise TransportTimeout(str(exc)) from exc
        except httpx.NetworkError as exc:
            raise TransportConnectionError(str(exc)) from exc
        except httpx.HTTPError as exc:
            raise TransportError(str(exc)) from exc

    def close(self) -> None:
        self._client.close()


# ---------------------------------------------------------------------------
# Transport factories
# ---------------------------------------------------------------------------


def wrap_async_transport(session: Any) -> AsyncTransport:
    """Wrap an existing async session/client in the appropriate transport.

    Auto-detects the type of *session* and returns the matching transport.
    If *session* already conforms to :class:`AsyncTransport` (has ``request``
    and ``close`` methods), it is returned as-is — this supports mock
    transports and custom implementations.

    Args:
        session: An ``aiohttp.ClientSession``, ``httpx.AsyncClient``, or any
            object conforming to :class:`AsyncTransport`.

    Raises:
        TypeError: If the session type is not recognized.
    """
    # Already a transport (mock, custom implementation, etc.)
    if isinstance(session, AsyncTransport):
        return session

    try:
        import aiohttp

        if isinstance(session, aiohttp.ClientSession):
            return AiohttpTransport(session)
    except ImportError:
        pass

    try:
        import httpx

        if isinstance(session, httpx.AsyncClient):
            return HttpxAsyncTransport(session)
    except ImportError:
        pass

    raise TypeError(
        f"Unsupported async transport: {type(session).__name__}. "
        f"Expected aiohttp.ClientSession, httpx.AsyncClient, or AsyncTransport."
    )


def wrap_sync_transport(session: Any) -> SyncTransport:
    """Wrap an existing sync session/client in the appropriate transport.

    If *session* already conforms to :class:`SyncTransport`, it is returned
    as-is — this supports mock transports and custom implementations.

    Args:
        session: A ``requests.Session``, ``httpx.Client``, or any object
            conforming to :class:`SyncTransport`.

    Raises:
        TypeError: If the session type is not recognized.
    """
    # Already a transport (mock, custom implementation, etc.)
    if isinstance(session, SyncTransport):
        return session

    try:
        import requests

        if isinstance(session, requests.Session):
            return RequestsTransport(session)
    except ImportError:
        pass

    try:
        import httpx

        if isinstance(session, httpx.Client):
            return HttpxSyncTransport(session)
    except ImportError:
        pass

    raise TypeError(
        f"Unsupported sync transport: {type(session).__name__}. "
        f"Expected requests.Session, httpx.Client, or SyncTransport."
    )


def create_async_transport(http_backend: str = "aiohttp") -> tuple[AsyncTransport, bool]:
    """Create a new async transport.

    Args:
        http_backend: ``"aiohttp"`` (default) or ``"httpx"``.

    Returns:
        A tuple of ``(transport, owns_session)`` where ``owns_session``
        is always ``True`` (the caller should close it).

    Raises:
        ValueError: If *http_backend* is not a recognized backend name.
    """
    if http_backend == "httpx":
        import httpx

        return HttpxAsyncTransport(httpx.AsyncClient()), True

    if http_backend == "aiohttp":
        import aiohttp

        return AiohttpTransport(aiohttp.ClientSession()), True

    raise ValueError(f"Unknown async http_backend: {http_backend!r}. Expected 'aiohttp' or 'httpx'.")


def create_sync_transport(http_backend: str = "requests") -> tuple[SyncTransport, bool]:
    """Create a new sync transport.

    Args:
        http_backend: ``"requests"`` (default) or ``"httpx"``.

    Returns:
        A tuple of ``(transport, owns_session)`` where ``owns_session``
        is always ``True``.

    Raises:
        ValueError: If *http_backend* is not a recognized backend name.
    """
    if http_backend == "httpx":
        import httpx

        return HttpxSyncTransport(httpx.Client()), True

    if http_backend == "requests":
        import requests

        return RequestsTransport(requests.Session()), True

    raise ValueError(f"Unknown sync http_backend: {http_backend!r}. Expected 'requests' or 'httpx'.")
