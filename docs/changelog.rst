Changelog
=========

0.1.0 (unreleased)
-------------------

Initial release.

- Async and sync clients for Etherscan, Routescan, and Blockscout
- Normalized Pydantic response models with hex coercion
- ``ProviderSet`` with ordered credentials, per-chain key scoping, shared rate limits
- Automatic provider fallback with ``FallbackWarning``
- ``response.provider`` indicates which explorer served each response
- Frontend URL builder with ``.urls`` and ``.urls_for(resp.provider)``
- Pluggable HTTP transport (aiohttp, requests, httpx)
- Transport injection for custom sessions
- Response cache with per-request ``force_refresh``
- Bundled chain registry (600+ chains) with offline lookup
- ``py.typed`` PEP 561 marker
- Python 3.10–3.14 support
