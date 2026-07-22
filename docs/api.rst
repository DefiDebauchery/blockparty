API Reference
=============

Clients
-------

.. autoclass:: blockparty.AsyncBlockpartyClient

.. autoclass:: blockparty.SyncBlockpartyClient

Client classes are documented above, and supported explorer methods are listed
explicitly by endpoint category below.

Explorer Endpoints
------------------

The explorer endpoint surface is available on both
``blockparty.AsyncBlockpartyClient`` and ``blockparty.SyncBlockpartyClient``.
All supported endpoints are listed below.

Account Endpoints
~~~~~~~~~~~~~~~~~

.. automethod:: blockparty.AsyncBlockpartyClient.get_normal_transactions
.. automethod:: blockparty.SyncBlockpartyClient.get_normal_transactions
.. automethod:: blockparty.AsyncBlockpartyClient.get_internal_transactions
.. automethod:: blockparty.SyncBlockpartyClient.get_internal_transactions
.. automethod:: blockparty.AsyncBlockpartyClient.get_internal_transactions_by_hash
.. automethod:: blockparty.SyncBlockpartyClient.get_internal_transactions_by_hash
.. automethod:: blockparty.AsyncBlockpartyClient.get_internal_transactions_by_block_range
.. automethod:: blockparty.SyncBlockpartyClient.get_internal_transactions_by_block_range
.. automethod:: blockparty.AsyncBlockpartyClient.get_erc20_token_transfers
.. automethod:: blockparty.SyncBlockpartyClient.get_erc20_token_transfers
.. automethod:: blockparty.AsyncBlockpartyClient.get_erc721_token_transfers
.. automethod:: blockparty.SyncBlockpartyClient.get_erc721_token_transfers
.. automethod:: blockparty.AsyncBlockpartyClient.get_erc1155_token_transfers
.. automethod:: blockparty.SyncBlockpartyClient.get_erc1155_token_transfers
.. automethod:: blockparty.AsyncBlockpartyClient.get_balance
.. automethod:: blockparty.SyncBlockpartyClient.get_balance
.. automethod:: blockparty.AsyncBlockpartyClient.get_historical_balance
.. automethod:: blockparty.SyncBlockpartyClient.get_historical_balance
.. automethod:: blockparty.AsyncBlockpartyClient.get_address_token_balance
.. automethod:: blockparty.SyncBlockpartyClient.get_address_token_balance
.. automethod:: blockparty.AsyncBlockpartyClient.get_address_nft_inventory
.. automethod:: blockparty.SyncBlockpartyClient.get_address_nft_inventory
.. automethod:: blockparty.AsyncBlockpartyClient.get_mined_blocks
.. automethod:: blockparty.SyncBlockpartyClient.get_mined_blocks
.. automethod:: blockparty.AsyncBlockpartyClient.get_beacon_withdrawals
.. automethod:: blockparty.SyncBlockpartyClient.get_beacon_withdrawals
.. automethod:: blockparty.AsyncBlockpartyClient.get_funded_by
.. automethod:: blockparty.SyncBlockpartyClient.get_funded_by
.. automethod:: blockparty.AsyncBlockpartyClient.get_deposit_transactions
.. automethod:: blockparty.SyncBlockpartyClient.get_deposit_transactions
.. automethod:: blockparty.AsyncBlockpartyClient.get_withdrawal_transactions
.. automethod:: blockparty.SyncBlockpartyClient.get_withdrawal_transactions
.. automethod:: blockparty.AsyncBlockpartyClient.get_plasma_deposits
.. automethod:: blockparty.SyncBlockpartyClient.get_plasma_deposits

Contract Endpoints
~~~~~~~~~~~~~~~~~~

.. automethod:: blockparty.AsyncBlockpartyClient.get_contract_abi
.. automethod:: blockparty.SyncBlockpartyClient.get_contract_abi
.. automethod:: blockparty.AsyncBlockpartyClient.get_contract_source_code
.. automethod:: blockparty.SyncBlockpartyClient.get_contract_source_code
.. automethod:: blockparty.AsyncBlockpartyClient.get_contract_creation
.. automethod:: blockparty.SyncBlockpartyClient.get_contract_creation

Transaction Endpoints
~~~~~~~~~~~~~~~~~~~~~

.. automethod:: blockparty.AsyncBlockpartyClient.get_transaction_status
.. automethod:: blockparty.SyncBlockpartyClient.get_transaction_status
.. automethod:: blockparty.AsyncBlockpartyClient.get_transaction_receipt_status
.. automethod:: blockparty.SyncBlockpartyClient.get_transaction_receipt_status

Block Endpoints
~~~~~~~~~~~~~~~

.. automethod:: blockparty.AsyncBlockpartyClient.get_block_reward
.. automethod:: blockparty.SyncBlockpartyClient.get_block_reward
.. automethod:: blockparty.AsyncBlockpartyClient.get_block_countdown
.. automethod:: blockparty.SyncBlockpartyClient.get_block_countdown
.. automethod:: blockparty.AsyncBlockpartyClient.get_block_no_by_time
.. automethod:: blockparty.SyncBlockpartyClient.get_block_no_by_time

Log Endpoints
~~~~~~~~~~~~~

.. automethod:: blockparty.AsyncBlockpartyClient.get_logs
.. automethod:: blockparty.SyncBlockpartyClient.get_logs

Token Endpoints
~~~~~~~~~~~~~~~

.. automethod:: blockparty.AsyncBlockpartyClient.get_token_balance
.. automethod:: blockparty.SyncBlockpartyClient.get_token_balance
.. automethod:: blockparty.AsyncBlockpartyClient.get_historical_token_balance
.. automethod:: blockparty.SyncBlockpartyClient.get_historical_token_balance
.. automethod:: blockparty.AsyncBlockpartyClient.get_token_supply
.. automethod:: blockparty.SyncBlockpartyClient.get_token_supply
.. automethod:: blockparty.AsyncBlockpartyClient.get_historical_token_supply
.. automethod:: blockparty.SyncBlockpartyClient.get_historical_token_supply
.. automethod:: blockparty.AsyncBlockpartyClient.get_token_holder_list
.. automethod:: blockparty.SyncBlockpartyClient.get_token_holder_list
.. automethod:: blockparty.AsyncBlockpartyClient.get_token_holder_count
.. automethod:: blockparty.SyncBlockpartyClient.get_token_holder_count
.. automethod:: blockparty.AsyncBlockpartyClient.get_token_info
.. automethod:: blockparty.SyncBlockpartyClient.get_token_info
.. automethod:: blockparty.AsyncBlockpartyClient.get_top_token_holders
.. automethod:: blockparty.SyncBlockpartyClient.get_top_token_holders

Gas Tracker Endpoints
~~~~~~~~~~~~~~~~~~~~~

.. automethod:: blockparty.AsyncBlockpartyClient.get_gas_oracle
.. automethod:: blockparty.SyncBlockpartyClient.get_gas_oracle
.. automethod:: blockparty.AsyncBlockpartyClient.get_gas_estimate
.. automethod:: blockparty.SyncBlockpartyClient.get_gas_estimate

Stats Endpoints
~~~~~~~~~~~~~~~

.. automethod:: blockparty.AsyncBlockpartyClient.get_eth_price
.. automethod:: blockparty.SyncBlockpartyClient.get_eth_price
.. automethod:: blockparty.AsyncBlockpartyClient.get_eth_supply
.. automethod:: blockparty.SyncBlockpartyClient.get_eth_supply
.. automethod:: blockparty.AsyncBlockpartyClient.get_eth_supply2
.. automethod:: blockparty.SyncBlockpartyClient.get_eth_supply2
.. automethod:: blockparty.AsyncBlockpartyClient.get_node_count
.. automethod:: blockparty.SyncBlockpartyClient.get_node_count
.. automethod:: blockparty.AsyncBlockpartyClient.get_daily_stats
.. automethod:: blockparty.SyncBlockpartyClient.get_daily_stats
.. automethod:: blockparty.AsyncBlockpartyClient.get_chain_size
.. automethod:: blockparty.SyncBlockpartyClient.get_chain_size
.. automethod:: blockparty.AsyncBlockpartyClient.get_eth_daily_price
.. automethod:: blockparty.SyncBlockpartyClient.get_eth_daily_price
.. automethod:: blockparty.AsyncBlockpartyClient.get_chainlist
.. automethod:: blockparty.SyncBlockpartyClient.get_chainlist

Pools
-----

.. autoclass:: blockparty.AsyncBlockpartyPool
   :members:

.. autoclass:: blockparty.SyncBlockpartyPool
   :members:

Shared pool helpers (inherited from ``BlockpartyPoolBase``):

.. automethod:: blockparty.AsyncBlockpartyPool.get_client
.. automethod:: blockparty.SyncBlockpartyPool.get_client

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
