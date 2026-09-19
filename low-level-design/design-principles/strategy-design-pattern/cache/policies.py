from collections import OrderedDict, defaultdict
from collections.abc import Callable, Hashable
from typing import Any

from .policy import EvictionPolicy


class UnknownPolicyError(LookupError):
    """No eviction policy is known under the requested name."""


def _oldest[K: Hashable](order: OrderedDict[K, None]) -> K:
    try:
        return next(iter(order))
    except StopIteration:
        raise LookupError("no entries to evict") from None


class FifoPolicy[K: Hashable](EvictionPolicy[K]):
    """First in, first out: evict the entry that has been in the cache longest."""

    def __init__(self) -> None:
        self._order: OrderedDict[K, None] = OrderedDict()

    def record_insert(self, key: K) -> None:
        self._order[key] = None

    def record_access(self, key: K) -> None:
        return  # reads do not change the order

    def record_remove(self, key: K) -> None:
        del self._order[key]

    def select_victim(self) -> K:
        return _oldest(self._order)


class LruPolicy[K: Hashable](EvictionPolicy[K]):
    """Least recently used: evict the entry that has gone unread the longest."""

    def __init__(self) -> None:
        self._order: OrderedDict[K, None] = OrderedDict()

    def record_insert(self, key: K) -> None:
        self._order[key] = None

    def record_access(self, key: K) -> None:
        self._order.move_to_end(key)  # now the most recently used

    def record_remove(self, key: K) -> None:
        del self._order[key]

    def select_victim(self) -> K:
        return _oldest(self._order)


class LfuPolicy[K: Hashable](EvictionPolicy[K]):
    """Least frequently used: evict the entry read the fewest times.

    Ties go to the entry that has waited longest at that count. Keys are grouped in
    buckets by read count, so recording an access is O(1).
    """

    def __init__(self) -> None:
        self._count: dict[K, int] = {}
        self._buckets: defaultdict[int, OrderedDict[K, None]] = defaultdict(OrderedDict)

    def record_insert(self, key: K) -> None:
        self._count[key] = 1
        self._buckets[1][key] = None

    def record_access(self, key: K) -> None:
        count = self._count[key]
        self._detach(key, count)
        self._count[key] = count + 1
        self._buckets[count + 1][key] = None

    def record_remove(self, key: K) -> None:
        self._detach(key, self._count.pop(key))

    def select_victim(self) -> K:
        if not self._buckets:
            raise LookupError("no entries to evict")
        return _oldest(self._buckets[min(self._buckets)])

    def _detach(self, key: K, count: int) -> None:
        bucket = self._buckets[count]
        del bucket[key]
        if not bucket:
            del self._buckets[count]


_POLICIES: dict[str, Callable[[], EvictionPolicy[Any]]] = {
    "fifo": FifoPolicy,
    "lfu": LfuPolicy,
    "lru": LruPolicy,
}


def make_policy[K: Hashable](name: str) -> EvictionPolicy[K]:
    """Build a fresh policy from a name, e.g. one read from a config file."""
    try:
        build = _POLICIES[name]
    except KeyError:
        available = ", ".join(sorted(_POLICIES))
        raise UnknownPolicyError(
            f"unknown eviction policy {name!r} (available: {available})"
        ) from None
    return build()
