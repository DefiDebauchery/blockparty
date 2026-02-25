Chain Registry
==============

blockparty bundles a snapshot of 600+ EVM chains with their explorer
configurations. The registry is loaded from a JSON file and provides
lookup, listing, and search.

.. code-block:: python

   from blockparty import ChainRegistry

   registry = ChainRegistry.load()

   entry = registry.get(8453)
   print(entry.name)        # "Base Mainnet"
   print(entry.is_testnet)  # False
   for explorer in entry.explorers:
       print(f"  {explorer.type}: {explorer.frontend_url}")

   matches = registry.search("base")

Custom registry file
--------------------

.. code-block:: python

   registry = ChainRegistry.load(path="/etc/myapp/chains.json")

Regenerating
------------

The bundled ``chains.json`` can be regenerated from the live Etherscan,
Routescan, and Blockscout APIs:

.. code-block:: bash

   python -m blockparty.registry.generate

This fetches current chain lists from all three providers, merges them,
resolves Routescan vanity URLs, and writes the result to
``src/blockparty/registry/data/chains.json``.

Chains where Routescan's ``publicApi`` flag is ``false`` are excluded
(they appear in Routescan's chain list but don't actually have API access).

Registry data model
-------------------

Each chain entry contains:

- ``chain_id`` — The EVM chain ID
- ``name`` — Human-readable chain name
- ``is_testnet`` — Whether it's a testnet
- ``explorers`` — List of ``ExplorerInfo`` objects, each with:

  - ``type`` — ``"etherscan"``, ``"routescan"``, or ``"blockscout"``
  - ``api_url`` — Full base URL for API calls
  - ``frontend_url`` — Human-facing explorer URL
  - ``frontend_url_vanity`` — Vanity hostname (Routescan only)
  - ``status`` — Etherscan chain status code (0/1/2)
  - ``hosted_by`` — Blockscout hosting indicator
