API Reference
=============

Clients
-------

.. autoclass:: blockparty.AsyncBlockpartyClient
   :members:
   :undoc-members:

.. autoclass:: blockparty.SyncBlockpartyClient
   :members:
   :undoc-members:

Pools
-----

.. autoclass:: blockparty.AsyncBlockpartyPool
   :members:

.. autoclass:: blockparty.SyncBlockpartyPool
   :members:

Provider Configuration
----------------------

.. autoclass:: blockparty.ProviderCredential
   :members:

.. autoclass:: blockparty.pool._base.ProviderSet
   :members:

Response Models
---------------

.. autoclass:: blockparty.ExplorerResponse
   :members:

.. autoclass:: blockparty.ScalarResponse
   :members:

.. autoclass:: blockparty.ObjectResponse
   :members:

.. autoclass:: blockparty.InternalTransaction
   :members:

.. autoclass:: blockparty.NormalTransaction
   :members:

.. autoclass:: blockparty.ERC20TokenTransfer
   :members:

.. autoclass:: blockparty.GasOracle
   :members:

.. autoclass:: blockparty.EthPrice
   :members:

.. autoclass:: blockparty.ContractSourceCode
   :members:

.. autoclass:: blockparty.EventLog
   :members:

URL Builder
-----------

.. autoclass:: blockparty.ExplorerURLs
   :members:

Chain Registry
--------------

.. autoclass:: blockparty.ChainRegistry
   :members:

.. autoclass:: blockparty.ChainEntry
   :members:

.. autoclass:: blockparty.ExplorerInfo
   :members:

Rate Limiting
-------------

.. autoclass:: blockparty.EtherscanTier
   :members:
   :undoc-members:

.. autoclass:: blockparty.RoutescanTier
   :members:
   :undoc-members:

.. autoclass:: blockparty.BlockscoutTier
   :members:
   :undoc-members:

.. autoclass:: blockparty.CustomRateLimit
   :members:

.. autoclass:: blockparty.ratelimit.budget.RateLimitBudget
   :members:

Transport
---------

.. autoclass:: blockparty.client._transport.AsyncTransport
   :members:

.. autoclass:: blockparty.client._transport.SyncTransport
   :members:

Exceptions
----------

.. autoclass:: blockparty.BlockpartyError
.. autoclass:: blockparty.ExplorerAPIError
.. autoclass:: blockparty.InvalidAPIKeyError
.. autoclass:: blockparty.RateLimitError
.. autoclass:: blockparty.InvalidAddressError
.. autoclass:: blockparty.PremiumEndpointError
.. autoclass:: blockparty.ChainNotSupportedError
.. autoclass:: blockparty.ChainNotFoundError
.. autoclass:: blockparty.ExplorerNotFoundError
.. autoclass:: blockparty.PoolExhaustedError
.. autoclass:: blockparty.ConfigurationError

Warnings
--------

.. autoclass:: blockparty.FallbackWarning
.. autoclass:: blockparty.AuthFallbackWarning
