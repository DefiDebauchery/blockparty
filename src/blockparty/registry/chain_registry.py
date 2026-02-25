"""Chain registry for looking up explorer configurations by chain ID.

The registry loads from a bundled ``chains.json`` snapshot (or a user-provided
path) and provides lookup, listing, search, and explorer-resolution methods.

Usage::

    registry = ChainRegistry.load()                              # bundled
    registry = ChainRegistry.load(path="/etc/myapp/chains.json") # custom

    entry = registry.get(8453)
    explorer = registry.get_explorer(8453, "etherscan")
"""

from __future__ import annotations

import json
from pathlib import Path

from blockparty._types import EXPLORER_PRIORITY, ExplorerType
from blockparty.exceptions import ChainNotFoundError, ExplorerNotFoundError
from blockparty.models.registry import ChainEntry, ExplorerInfo

_BUNDLED_DATA = Path(__file__).parent / "data" / "chains.json"


class ChainRegistry:
    """In-memory chain registry backed by a JSON snapshot.

    Instances are created via :meth:`load` and are immutable after construction.
    """

    __slots__ = ("_by_id", "_entries")

    def __init__(self, entries: list[ChainEntry]) -> None:
        self._entries = entries
        self._by_id: dict[int, ChainEntry] = {e.chain_id: e for e in entries}

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path | None = None) -> ChainRegistry:
        """Load the registry from a JSON file.

        Args:
            path: Path to a ``chains.json`` file.  If ``None``, the bundled
                snapshot shipped with the package is used.

        Returns:
            A new :class:`ChainRegistry` instance.

        Raises:
            FileNotFoundError: If *path* does not exist.
            ValueError: If the JSON is malformed or cannot be parsed.
        """
        target = Path(path) if path is not None else _BUNDLED_DATA
        raw = json.loads(target.read_text(encoding="utf-8"))
        entries = [ChainEntry.model_validate(item) for item in raw]
        return cls(entries)

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def get(self, chain_id: int) -> ChainEntry:
        """Get a chain entry by ID.

        Raises:
            ChainNotFoundError: If the chain ID is not in the registry.
        """
        try:
            return self._by_id[chain_id]
        except KeyError:
            raise ChainNotFoundError(chain_id) from None

    def list_chains(self) -> list[ChainEntry]:
        """Return all chain entries, ordered by chain ID."""
        return sorted(self._entries, key=lambda e: e.chain_id)

    def search(self, query: str) -> list[ChainEntry]:
        """Search chains by name (case-insensitive substring match).

        Args:
            query: The search string.

        Returns:
            Matching chain entries, ordered by chain ID.
        """
        q = query.lower()
        return sorted(
            (e for e in self._entries if q in e.name.lower()),
            key=lambda e: e.chain_id,
        )

    def get_explorer(
        self,
        chain_id: int,
        explorer_type: ExplorerType | None = None,
    ) -> ExplorerInfo:
        """Resolve the best explorer for a chain.

        Args:
            chain_id: The EVM chain ID.
            explorer_type: If provided, return that specific explorer type.
                If ``None``, return the highest-priority available explorer
                (Etherscan > Routescan > Blockscout).

        Returns:
            The resolved :class:`ExplorerInfo`.

        Raises:
            ChainNotFoundError: If the chain ID is not in the registry.
            ExplorerNotFoundError: If no matching explorer is available.
        """
        entry = self.get(chain_id)
        explorers_by_type = {e.type: e for e in entry.explorers}

        if explorer_type is not None:
            if explorer_type in explorers_by_type:
                return explorers_by_type[explorer_type]
            raise ExplorerNotFoundError(chain_id, explorer_type)

        # Auto-resolve by priority order.
        for ptype in EXPLORER_PRIORITY:
            if ptype in explorers_by_type:
                return explorers_by_type[ptype]

        raise ExplorerNotFoundError(chain_id)

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, chain_id: int) -> bool:
        return chain_id in self._by_id

    def __repr__(self) -> str:
        return f"ChainRegistry({len(self._entries)} chains)"
