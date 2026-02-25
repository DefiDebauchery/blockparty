Shared Providers
================

``ProviderSet`` is the key to sharing rate limits and credentials across
multiple clients. When multiple clients share a ``ProviderSet``, identical
``(provider, api_key)`` pairs automatically share one rate limit budget.

Multi-chain with shared rate limits
------------------------------------

.. code-block:: python

   import asyncio
   from blockparty import (
       AsyncBlockpartyClient,
       ProviderSet,
       ProviderCredential,
       EtherscanTier,
       RoutescanTier,
   )

   providers = ProviderSet([
       ProviderCredential(
           type="etherscan",
           api_key="YOUR_KEY",
           tier=EtherscanTier.STANDARD,
       ),
       ProviderCredential(type="routescan", tier=RoutescanTier.ANONYMOUS),
       ProviderCredential(type="blockscout"),
   ])

   # All clients share one rate limit budget for ("etherscan", "YOUR_KEY")
   clients = {
       "base": AsyncBlockpartyClient(chain_id=8453, providers=providers),
       "arbitrum": AsyncBlockpartyClient(chain_id=42161, providers=providers),
       "optimism": AsyncBlockpartyClient(chain_id=10, providers=providers),
   }

   results = await asyncio.gather(*[
       c.get_internal_transactions(address="0x...")
       for c in clients.values()
   ])

   for c in clients.values():
       await c.close()

Per-chain API keys
------------------

.. code-block:: python

   providers = ProviderSet([
       # Premium key for Base and Optimism only
       ProviderCredential(
           type="etherscan",
           api_key="PREMIUM_KEY",
           tier=EtherscanTier.STANDARD,
           chain_ids=frozenset({8453, 10}),
       ),
       # Free key for everything else
       ProviderCredential(
           type="etherscan",
           api_key="FREE_KEY",
           tier=EtherscanTier.FREE,
       ),
       # Anonymous fallbacks
       ProviderCredential(type="routescan"),
       ProviderCredential(type="blockscout"),
   ])

When a client for chain 8453 runs, it tries ``PREMIUM_KEY`` first (matches via
``chain_ids``), then ``FREE_KEY`` (matches all chains), then Routescan, then
Blockscout. A client for chain 42161 skips ``PREMIUM_KEY`` (not in its
``chain_ids``) and starts with ``FREE_KEY``.

Provider fallback
-----------------

Every client with multiple providers in its ``ProviderSet`` automatically
falls back on transient errors (rate limits, 5xx, auth failures):

.. code-block:: python

   # If Etherscan rate-limits or is down, Routescan is tried next
   async with AsyncBlockpartyClient(chain_id=8453, providers=providers) as client:
       response = await client.get_internal_transactions(address="0x...")

Non-recoverable errors (invalid address, premium-only endpoint) raise immediately
without trying other providers.

Every response includes ``response.provider`` indicating which explorer
actually served the data. See :doc:`urls` for how to generate URLs matching
the actual provider.

Handling fallback warnings
--------------------------

.. code-block:: python

   import warnings
   import logging
   from blockparty import FallbackWarning

   # Route warnings to the logging system
   logging.captureWarnings(True)

   # Or escalate to exceptions
   warnings.filterwarnings("error", category=FallbackWarning)
