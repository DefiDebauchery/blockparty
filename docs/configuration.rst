Client Configuration
====================

Explicit explorer and API key
-----------------------------

.. code-block:: python

   from blockparty import AsyncBlockpartyClient, EtherscanTier

   async with AsyncBlockpartyClient(
       chain_id=8453,
       explorer_type="etherscan",
       api_key="YOUR_ETHERSCAN_KEY",
       tier=EtherscanTier.STANDARD,
   ) as client:
       response = await client.get_internal_transactions(address="0x...")

Without an API key
------------------

No key required — auto-resolves to the best available explorer
(priority: Etherscan > Routescan > Blockscout):

.. code-block:: python

   async with AsyncBlockpartyClient(chain_id=8453) as client:
       response = await client.get_internal_transactions(address="0x...")

Tuning cache
------------

.. code-block:: python

   client = AsyncBlockpartyClient(
       chain_id=8453,
       cache_ttl=60,       # Cache responses for 60 seconds (default: 30, 0 disables)
   )

Force-refresh a cached response
--------------------------------

.. code-block:: python

   response = await client.get_internal_transactions(
       address="0x...",
       force_refresh=True,
   )

Using httpx instead of aiohttp
------------------------------

.. code-block:: python

   async with AsyncBlockpartyClient(chain_id=8453, http_backend="httpx") as client:
       response = await client.get_internal_transactions(address="0x...")

Passing a pre-configured transport
-----------------------------------

.. code-block:: python

   import httpx

   # You control the session lifecycle
   my_http = httpx.AsyncClient(timeout=60, proxy="http://proxy:8080")
   async with AsyncBlockpartyClient(chain_id=8453, transport=my_http) as client:
       response = await client.get_internal_transactions(address="0x...")
   # blockparty does NOT close my_http — you do
   await my_http.aclose()

Any object conforming to the ``AsyncTransport`` protocol (``request()`` and
``close()`` methods) is accepted, including mocks for testing.
