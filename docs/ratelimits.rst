Rate Limits & Tiers
===================

blockparty enforces per-``(provider, api_key)`` rate limiting using a token
bucket algorithm. Rate limit budgets are shared across all clients that use
the same credential (via ``ProviderSet`` or the same ``RateLimitRegistry``).

Provider tiers
--------------

Each provider has built-in tier enums encoding their known plan limits:

.. list-table::
   :header-rows: 1
   :widths: 20 25 10 15

   * - Provider
     - Tier
     - RPS
     - RPD
   * - Etherscan
     - ``FREE``
     - 3
     - 100,000
   * - Etherscan
     - ``LITE``
     - 5
     - 100,000
   * - Etherscan
     - ``STANDARD``
     - 10
     - 200,000
   * - Etherscan
     - ``ADVANCED``
     - 20
     - 500,000
   * - Etherscan
     - ``PROFESSIONAL``
     - 30
     - 1,000,000
   * - Routescan
     - ``ANONYMOUS`` (no key)
     - 2
     - 10,000
   * - Routescan
     - ``FREE``
     - 5
     - 100,000
   * - Routescan
     - ``STANDARD``
     - 10
     - 200,000
   * - Routescan
     - ``ADVANCED``
     - 20
     - 500,000
   * - Routescan
     - ``PROFESSIONAL``
     - 30
     - 1,000,000
   * - Routescan
     - ``PRO_PLUS``
     - 30
     - 1,500,000
   * - Blockscout
     - ``ANONYMOUS``
     - ~5
     - —
   * - Blockscout
     - ``KEYED``
     - ~10
     - —

Custom rate limits
------------------

For enterprise plans or non-standard limits:

.. code-block:: python

   from blockparty import AsyncBlockpartyClient, CustomRateLimit

   client = AsyncBlockpartyClient(
       chain_id=8453,
       explorer_type="etherscan",
       api_key="ENTERPRISE_KEY",
       tier=CustomRateLimit(rps=50, rpd=2_000_000),
   )

Blockscout adaptive limits
--------------------------

Blockscout communicates rate limits dynamically via response headers
(``X-Ratelimit-Limit``, ``X-Ratelimit-Remaining``, ``X-Ratelimit-Reset``).
The ``RateLimitBudget`` adapts its token bucket capacity from these headers
on every response, so the initial tier value is only used until the first
successful call.
