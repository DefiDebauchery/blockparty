# Contributing to blockparty

## Development Setup

```bash
git clone https://github.com/your-org/blockparty.git
cd blockparty
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest                    # full suite
pytest tests/ -v          # verbose
pytest tests/ -k "async"  # filter by name
```

All tests run without network access using mock transports.
The `live_test.py` script exercises real APIs — run it manually
to verify end-to-end behavior:

```bash
python live_test.py
ETHERSCAN_API_KEY=your_key python live_test.py
```

## Linting

```bash
ruff check src/ tests/    # lint
ruff format src/ tests/   # auto-format
```

CI runs both on every push. Fix all issues before submitting a PR.

## Adding a New Endpoint

Every API endpoint is defined once in `ENDPOINT_REGISTRY` and then exposed
as an explicit method on both client classes. Adding a new endpoint
requires touching three files — no changes to the transport, caching, rate
limiting, or fallback logic.

### Step 1: Define the response model (if needed)

If the endpoint returns a new data shape, add a Pydantic model in
`src/blockparty/models/responses.py`:

```python
class NewThing(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    some_field: CoercedInt = Field(alias="someField")
    other_field: str = Field(alias="otherField")
```

If the endpoint returns a scalar (single string) or reuses an existing model,
skip this step.

### Step 2: Register the endpoint

In `src/blockparty/client/_endpoints.py`, add an entry to `ENDPOINT_REGISTRY`:

```python
"get_new_thing": Endpoint(
    module="account",                     # Etherscan module
    action="getnewthings",                # Etherscan action
    shape=ResponseShape.LIST,             # LIST, SCALAR, OBJECT, or INTERNAL_TX
    model=NewThing,                       # Pydantic model (None for SCALAR)
    params=[
        ParamSpec("contractaddress", "contract_address"),  # api_name, python_name
        ParamSpec("address"),                              # same name in both
        *_PAGINATION,                                      # page + limit
        _SORT,                                             # sort
    ],
),
```

The `ParamSpec` handles name translation. The developer writes
`contract_address="0x..."`, the API receives `contractaddress=0x...`.
`_PAGINATION` expands to `[ParamSpec("page"), ParamSpec("offset", "limit")]`
so the developer writes `limit=10` and the API receives `offset=10`.

### Step 3: Add the method to both clients

In `src/blockparty/client/async_client.py`:

```python
async def get_new_thing(
    self,
    contract_address: str,
    address: str,
    page: int = 1,
    limit: int = 10,
    sort: Literal["asc", "desc"] = "asc",
    *,
    force_refresh: bool = False,
) -> ExplorerResponse[NewThing]:
    """Fetch new things for a contract and address."""
    return await self._execute(
        "get_new_thing", force_refresh=force_refresh,
        contract_address=contract_address, address=address,
        page=page, limit=limit, sort=sort,
    )
```

The sync client in `sync_client.py` is identical but without `async`/`await`.

The method signature is the entire IDE experience — autocomplete, type hints,
docstrings. The body is always a one-liner delegating to `_execute()` with
the registry key. Everything else (param mapping, rate limiting, fallback,
caching, provider stamping) happens automatically.

### Checklist

- [ ] Response model in `models/responses.py` (if new shape)
- [ ] Export the model from `models/__init__.py` and `__init__.py`
- [ ] Entry in `ENDPOINT_REGISTRY` in `client/_endpoints.py`
- [ ] Method on `AsyncBlockpartyClient` in `client/async_client.py`
- [ ] Mirror method on `SyncBlockpartyClient` in `client/sync_client.py`
- [ ] Test in `tests/test_client_endpoints.py` (verify param mapping)
- [ ] Optionally: method on pool classes (if commonly used with multi-chain)

## Conventions

- **Python ≥ 3.10.** Use `X | Y` unions with `from __future__ import annotations`.
  No PEP 695 (`class Foo[T]`) — use `Generic[T]` + `TypeVar` for 3.10 compat.
- **Pydantic v2.** `model_config` not `class Config`.
- **Param naming.** Developer-facing: `start_block`, `contract_address`, `limit`.
  API-facing: `startblock`, `contractaddress`, `offset`.
- **Docstrings.** Google style on every public class and method. Sphinx reads these
  directly.
- **Tests.** Every test should exercise actual logic. Don't test string constants,
  Pydantic field defaults, or `repr` output.
