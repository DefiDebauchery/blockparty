# blockparty

A unified Python client for EVM block explorer APIs — **Etherscan**, **Routescan**, and **Blockscout**.

Normalizes responses across providers, supports both sync and async usage, provides
automatic fallback across providers, and builds frontend explorer URLs.

## Installation

```bash
pip install blockparty
```

For httpx support:

```bash
pip install "blockparty[httpx]"
```

Requires **Python ≥ 3.10**.

## Features

- **Multi-provider support** — Etherscan, Routescan, and Blockscout behind one API
- **Normalized responses** — Consistent Pydantic models regardless of which explorer answered
- **Sync and async** — `SyncBlockpartyClient` and `AsyncBlockpartyClient`
- **Provider fallback** — Clients try providers in order, automatically falling back on transient errors
- **Shared rate limiting** — Per-`(provider, api_key)` token bucket shared across all clients via `ProviderSet`
- **Pluggable HTTP backend** — aiohttp + requests (default) or httpx (optional)
- **Transport injection** — Pass your own `aiohttp.ClientSession` or `httpx.AsyncClient`
- **Response caching** — Configurable TTL, per-request `force_refresh` override
- **Retry with backoff** — Exponential backoff + jitter on transient errors
- **Frontend URL builder** — Generate explorer links for addresses, transactions, tokens, and blocks
- **Bundled chain registry** — 600+ chains with offline lookup and CLI regeneration

## Quick Start

### Async

```python
from blockparty import AsyncBlockpartyClient

async with AsyncBlockpartyClient(chain_id=8453) as client:
    response = await client.get_internal_transactions(
        address="0x4200000000000000000000000000000000000006",
        start_block=7775467,
        limit=10,
        sort="asc",
    )
    for tx in response.result:
        print(f"{tx.hash}: {tx.value} wei")
```

### Sync

```python
from blockparty import SyncBlockpartyClient

with SyncBlockpartyClient(chain_id=8453) as client:
    response = client.get_internal_transactions(address="0x...", limit=10)
```

No API key required — blockparty auto-resolves to the best available explorer
(priority: Etherscan > Routescan > Blockscout).

## What Else It Does

**[Client configuration](https://blockparty.readthedocs.io/en/latest/configuration.html)** —
Explicit explorer types, API keys, tier selection, httpx backend, transport
injection, cache tuning.

**[Shared providers](https://blockparty.readthedocs.io/en/latest/providers.html)** —
`ProviderSet` shares rate limit budgets across clients, supports per-chain API
keys via `chain_ids`, and gives every client automatic fallback with
`FallbackWarning`.

**[Connection pool](https://blockparty.readthedocs.io/en/latest/pool.html)** —
`AsyncBlockpartyPool` / `SyncBlockpartyPool` caches clients per chain and
delegates all fallback logic to `ProviderSet`.

**[URL builder](https://blockparty.readthedocs.io/en/latest/urls.html)** —
`.urls` for the preferred explorer, `.urls_for(resp.provider)` for the
explorer that actually served a response. Supports Etherscan, Routescan
(vanity + generic), and Blockscout.

**[Chain registry](https://blockparty.readthedocs.io/en/latest/registry.html)** —
600+ chains bundled, offline lookup by ID or name search, custom JSON files,
CLI regeneration.

**[Rate limits & tiers](https://blockparty.readthedocs.io/en/latest/ratelimits.html)** —
Built-in tier enums for all three providers, `CustomRateLimit` for enterprise
plans, Blockscout adaptive headers.

## Development

```bash
git clone https://github.com/your-org/blockparty.git
cd blockparty
pip install -e ".[dev]"
pytest
ruff check src/ tests/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add new endpoints,
run tests, and submit changes.

## License

MIT
