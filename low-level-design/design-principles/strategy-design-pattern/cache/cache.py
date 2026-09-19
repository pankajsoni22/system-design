from collections.abc import Callable, Hashable
from dataclasses import dataclass

from .policy import EvictionPolicy


def one_per_entry(key: object, value: object) -> int:
    """The default weigher: every entry costs 1, so capacity counts entries."""
    return 1


@dataclass(frozen=True, slots=True)
class CacheStats:
    hits: int
    misses: int
    evictions: int

    @property
    def hit_rate(self) -> float:
        lookups = self.hits + self.misses
        return self.hits / lookups if lookups else 0.0


class Cache[K: Hashable, V]:
    """The context: stores entries and delegates "who goes?" to an eviction policy.

    Not thread-safe: guard it with a lock if several threads share one cache.
    """

    def __init__(
        self,
        capacity: int,
        policy: EvictionPolicy[K],
        weigher: Callable[[K, V], int] = one_per_entry,
    ) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._capacity = capacity
        self._policy = policy
        self._weigher = weigher
        self._data: dict[K, tuple[V, int]] = {}  # key -> (value, weight)
        self._used = 0
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: K, default: V | None = None) -> V | None:
        entry = self._data.get(key)
        if entry is None:
            self._misses += 1
            return default
        self._hits += 1
        self._policy.record_access(key)
        return entry[0]

    def put(self, key: K, value: V) -> None:
        weight = self._weigher(key, value)
        if weight < 1:
            raise ValueError(f"an entry must weigh at least 1, got {weight}")
        if weight > self._capacity:
            raise ValueError(
                f"entry weighs {weight}, more than the capacity {self._capacity}"
            )

        self.delete(key)  # overwriting replaces the entry, and its history restarts
        while self._used + weight > self._capacity:
            self._remove(self._policy.select_victim())
            self._evictions += 1
        self._data[key] = (value, weight)
        self._used += weight
        self._policy.record_insert(key)

    def delete(self, key: K) -> bool:
        if key not in self._data:
            return False
        self._remove(key)
        return True

    def set_policy(self, policy: EvictionPolicy[K]) -> None:
        """Swap the strategy at run time. Recency and counts start again from zero."""
        self._policy = policy
        for key in self._data:  # oldest stored first
            policy.record_insert(key)

    @property
    def policy(self) -> EvictionPolicy[K]:
        return self._policy

    @property
    def used(self) -> int:
        return self._used

    @property
    def stats(self) -> CacheStats:
        return CacheStats(self._hits, self._misses, self._evictions)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: object) -> bool:
        return key in self._data  # a peek: not a hit, not an access

    def _remove(self, key: K) -> None:
        _, weight = self._data.pop(key)
        self._used -= weight
        self._policy.record_remove(key)
