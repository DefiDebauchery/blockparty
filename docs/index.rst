blockparty
==========

A unified Python client for EVM block explorer APIs — **Etherscan**,
**Routescan**, and **Blockscout**.

.. code-block:: python

   from blockparty import AsyncBlockpartyClient

   async with AsyncBlockpartyClient(chain_id=8453) as client:
       resp = await client.get_internal_transactions(address="0x...", limit=10)
       print(resp.provider)  # "etherscan", "routescan", or "blockscout"
       for tx in resp.result:
           print(tx.hash, tx.value)

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   configuration
   providers
   pool
   urls
   registry
   ratelimits

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api

.. toctree::
   :maxdepth: 1
   :caption: Project

   changelog
