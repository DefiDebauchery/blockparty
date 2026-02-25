Connection Pool
===============

``AsyncBlockpartyPool`` and ``SyncBlockpartyPool`` are convenience wrappers
that create and cache clients per chain. They use a ``ProviderSet`` under the
hood, so all fallback and rate limiting works automatically.

.. code-block:: python

   from blockparty import AsyncBlockpartyPool, ProviderCredential, EtherscanTier

   async with AsyncBlockpartyPool(
       credentials=[
           ProviderCredential(type="etherscan", api_key="KEY", tier=EtherscanTier.STANDARD),
           ProviderCredential(type="routescan"),
           ProviderCredential(type="blockscout"),
       ],
   ) as pool:
       base_txs = await pool.get_internal_transactions(chain_id=8453, address="0x...", limit=10)
       arb_txs = await pool.get_internal_transactions(chain_id=42161, address="0x...", limit=10)

       # URL for preferred explorer
       print(pool.urls(8453).tx("0xabc123..."))

       # URL for the explorer that actually answered
       print(pool.urls_for(8453, base_txs.provider).tx("0xabc123..."))

You can also pass an existing ``ProviderSet``:

.. code-block:: python

   pool = AsyncBlockpartyPool(providers=my_provider_set)

Sync pool
---------

.. code-block:: python

   from blockparty import SyncBlockpartyPool, ProviderCredential

   with SyncBlockpartyPool(
       credentials=[
           ProviderCredential(type="routescan"),
           ProviderCredential(type="blockscout"),
       ],
   ) as pool:
       resp = pool.get_internal_transactions(chain_id=8453, address="0x...", limit=10)
