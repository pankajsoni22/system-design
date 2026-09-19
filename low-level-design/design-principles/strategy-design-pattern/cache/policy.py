from abc import ABC, abstractmethod
from collections.abc import Hashable


class EvictionPolicy[K: Hashable](ABC):
    """The strategy: decides *which* entry to evict when the cache is full.

    A policy keeps its own bookkeeping and sees only keys, never values. Each cache
    needs its own policy instance, because the bookkeeping describes that cache's entries.
    """

    @abstractmethod
    def record_insert(self, key: K) -> None:
        """A new key was stored."""

    @abstractmethod
    def record_access(self, key: K) -> None:
        """A stored key was read (a cache hit)."""

    @abstractmethod
    def record_remove(self, key: K) -> None:
        """A key left the cache, by eviction or by deletion."""

    @abstractmethod
    def select_victim(self) -> K:
        """Return the key to evict next. Raise `LookupError` if there is none."""
