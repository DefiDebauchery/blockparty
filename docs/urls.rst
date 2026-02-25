Frontend URL Builder
====================

Every client exposes a ``.urls`` property that generates human-facing explorer
links for addresses, transactions, tokens, and blocks.

.. code-block:: python

   async with AsyncBlockpartyClient(chain_id=8453) as client:
       print(client.urls.address("0x88D19A..."))  # https://basescan.org/address/0x88D19A...
       print(client.urls.tx("0xabc123..."))       # https://basescan.org/tx/0xabc123...
       print(client.urls.token("0x4200...0006"))  # https://basescan.org/token/0x4200...
       print(client.urls.block(7796207))          # https://basescan.org/block/7796207
       print(client.urls.blocks())                # https://basescan.org/blocks

``.urls`` always returns URLs for the **preferred** (first) explorer in the
client's provider list.

URLs from the actual provider
-----------------------------

After a fallback, the preferred explorer may not be the one that answered.
Use ``.urls_for(resp.provider)`` to get URLs matching the explorer that
actually served the response:

.. code-block:: python

   resp = await client.get_internal_transactions(address="0x...", limit=10)

   print(resp.provider)  # "blockscout" (after Etherscan failed)

   # Preferred explorer — stable, always the same
   print(client.urls.tx(resp.result[0].hash))
   # → https://basescan.org/tx/0xabc...

   # Actual provider — matches who answered
   print(client.urls_for(resp.provider).tx(resp.result[0].hash))
   # → https://base.blockscout.com/tx/0xabc...

The pool version takes ``chain_id`` as the first argument:

.. code-block:: python

   resp = await pool.get_internal_transactions(chain_id=8453, address="0x...")
   urls = pool.urls_for(8453, resp.provider)

Passing ``None`` (or an unrecognized type) falls back to the preferred
explorer, so ``client.urls_for(None)`` is equivalent to ``client.urls``.

Routescan URL behavior
----------------------

Routescan URLs prefer vanity hostnames (e.g. ``basescan.routescan.io``) when
available in the chain registry. When no vanity hostname exists, URLs fall back
to the generic pattern (``routescan.io/address/0x...?chainid=8453``).

Block URLs (``/block/N``) always include ``chainid`` even on vanity hosts,
per Routescan's requirements.

Testnet chains use ``testnet.routescan.io`` as the generic hostname.
