"""Fetch and parse chain data from explorer provider APIs.

Each provider has a public API that lists supported chains.  This module
fetches from all three, normalizes the data into :class:`ChainEntry` /
:class:`ExplorerInfo` objects, and merges them by chain ID.

Used by :mod:`blockparty.registry.generate` to produce the bundled snapshot.
"""

from __future__ import annotations

from typing import Any

import aiohttp

from blockparty.models.registry import ChainEntry, ExplorerInfo

# ---------------------------------------------------------------------------
# Etherscan — GET https://api.etherscan.io/v2/chainlist
# ---------------------------------------------------------------------------

ETHERSCAN_CHAINLIST_URL = "https://api.etherscan.io/v2/chainlist"


async def fetch_etherscan_chains(
    session: aiohttp.ClientSession,
) -> list[ChainEntry]:
    """Fetch the Etherscan chain list and return parsed entries."""
    async with session.get(ETHERSCAN_CHAINLIST_URL) as resp:
        resp.raise_for_status()
        data = await resp.json()

    entries: list[ChainEntry] = []
    for item in data.get("result", []):
        chain_id = int(item["chainid"])
        name = item.get("chainname", f"Chain {chain_id}")
        is_testnet = "testnet" in name.lower()

        explorer = ExplorerInfo(
            type="etherscan",
            api_url=item.get("apiurl", f"https://api.etherscan.io/v2/api?chainid={chain_id}"),
            frontend_url=item.get("blockexplorer", ""),
            frontend_url_vanity=None,
            status=item.get("status"),
            hosted_by=None,
        )
        entries.append(
            ChainEntry(
                chain_id=chain_id,
                name=name,
                is_testnet=is_testnet,
                explorers=[explorer],
            )
        )

    return entries


# ---------------------------------------------------------------------------
# Routescan — GET https://api.routescan.io/v2/network/{net}/evm/all/blockchains
# ---------------------------------------------------------------------------

ROUTESCAN_CHAINS_URL = "https://api.routescan.io/v2/network/{net}/evm/all/blockchains"


async def fetch_routescan_chains(
    session: aiohttp.ClientSession,
    *,
    network: str = "mainnet",
) -> list[ChainEntry]:
    """Fetch the Routescan chain list for a given network type."""
    url = ROUTESCAN_CHAINS_URL.format(net=network)
    is_testnet = network == "testnet"

    async with session.get(url) as resp:
        resp.raise_for_status()
        data = await resp.json()

    entries: list[ChainEntry] = []
    for item in data.get("items", []):
        chain_id_raw = item.get("evmChainId") or item.get("chainId")
        if not chain_id_raw:
            continue
        chain_id = int(chain_id_raw)
        if not item.get("publicApi"):
            continue
        name = item.get("name", f"Chain {chain_id}")

        api_url = f"https://api.routescan.io/v2/network/{network}/evm/{chain_id}/etherscan/api"

        frontend_base = "https://testnet.routescan.io" if is_testnet else "https://routescan.io"

        explorer = ExplorerInfo(
            type="routescan",
            api_url=api_url,
            frontend_url=frontend_base,
            frontend_url_vanity=None,
            status=None,
            hosted_by=None,
        )
        entries.append(
            ChainEntry(
                chain_id=chain_id,
                name=name,
                is_testnet=is_testnet,
                explorers=[explorer],
            )
        )

    return entries


# ---------------------------------------------------------------------------
# Blockscout — GET https://chains.blockscout.com/api/chains
# ---------------------------------------------------------------------------

BLOCKSCOUT_CHAINS_URL = "https://chains.blockscout.com/api/chains"


async def fetch_blockscout_chains(
    session: aiohttp.ClientSession,
) -> list[ChainEntry]:
    """Fetch the Blockscout chain list and return parsed entries."""
    async with session.get(BLOCKSCOUT_CHAINS_URL) as resp:
        resp.raise_for_status()
        data = await resp.json()

    entries: list[ChainEntry] = []

    # Blockscout returns a dict keyed by chain_id, or a list — handle both.
    items: list[tuple[str, dict[str, Any]]]
    if isinstance(data, dict):
        items = list(data.items())
    elif isinstance(data, list):
        items = [(str(item.get("id", "")), item) for item in data]
    else:
        return entries

    for chain_id_str, item in items:
        try:
            chain_id = int(chain_id_str)
        except (ValueError, TypeError):
            continue

        name = item.get("name", f"Chain {chain_id}")
        is_testnet = bool(item.get("isTestnet", False))

        explorer_list = item.get("explorers", [])
        explorers: list[ExplorerInfo] = []
        for exp in explorer_list:
            url = exp.get("url", "").rstrip("/")
            if not url:
                continue
            hosted_by = exp.get("hostedBy", None)
            explorers.append(
                ExplorerInfo(
                    type="blockscout",
                    api_url=f"{url}/api",
                    frontend_url=f"{url}/",
                    frontend_url_vanity=None,
                    status=None,
                    hosted_by=hosted_by,
                )
            )

        if explorers:
            entries.append(
                ChainEntry(
                    chain_id=chain_id,
                    name=name,
                    is_testnet=is_testnet,
                    explorers=explorers,
                )
            )

    return entries


# ---------------------------------------------------------------------------
# Routescan vanity URL API
# ---------------------------------------------------------------------------

ROUTESCAN_VANITY_URL = "https://routescan.io/api/vanity-urls"


async def fetch_routescan_vanity_urls(
    session: aiohttp.ClientSession,
) -> dict[int, str]:
    """Fetch vanity hostname mappings from the Routescan vanity-urls API.

    The endpoint returns ``{"items": [{"chainId": "...", "url": "..."}, ...]}``.
    Each ``url`` is a bare hostname (no scheme); HTTPS is assumed.

    Returns:
        A dict mapping chain ID → vanity base URL
        (e.g., ``{8453: "https://basescan.routescan.io"}``).
    """
    async with session.get(ROUTESCAN_VANITY_URL) as resp:
        resp.raise_for_status()
        data = await resp.json()

    vanity_map: dict[int, str] = {}
    for item in data.get("items", []):
        try:
            chain_id = int(item["chainId"])
        except (KeyError, ValueError, TypeError):
            continue
        hostname = item.get("url", "").strip().rstrip("/")
        if hostname:
            # Ensure scheme is present
            if not hostname.startswith(("http://", "https://")):
                hostname = f"https://{hostname}"
            vanity_map[chain_id] = hostname

    return vanity_map


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------


def merge_chain_entries(sources: list[list[ChainEntry]]) -> list[ChainEntry]:
    """Merge chain entries from multiple sources, deduplicating by chain ID.

    When multiple sources provide data for the same chain, their explorer
    lists are combined.  Name and testnet status use a majority vote when
    sources disagree; single-source chains trust that source.

    Args:
        sources: A list of entry lists, one per provider source.

    Returns:
        Merged, deduplicated chain entries sorted by chain ID.
    """
    by_id: dict[int, list[ChainEntry]] = {}
    for source in sources:
        for entry in source:
            by_id.setdefault(entry.chain_id, []).append(entry)

    merged: list[ChainEntry] = []
    for chain_id, candidates in sorted(by_id.items()):
        # Collect all explorers from all sources.
        all_explorers: list[ExplorerInfo] = []
        for c in candidates:
            all_explorers.extend(c.explorers)

        # Majority vote on name (prefer longest / most descriptive).
        name = max(
            (c.name for c in candidates),
            key=len,
        )

        # Majority vote on testnet.
        testnet_votes = [c.is_testnet for c in candidates]
        is_testnet = sum(testnet_votes) > len(testnet_votes) / 2

        merged.append(
            ChainEntry(
                chain_id=chain_id,
                name=name,
                is_testnet=is_testnet,
                explorers=all_explorers,
            )
        )

    return merged
