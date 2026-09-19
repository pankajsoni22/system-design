from collections import OrderedDict

import pytest

from cache import Cache, EvictionPolicy, LruPolicy


class MruPolicy(EvictionPolicy[str]):
    """Most recently used goes first. Defined here, outside the library."""

    def __init__(self) -> None:
        self._order: OrderedDict[str, None] = OrderedDict()

    def record_insert(self, key: str) -> None:
        self._order[key] = None

    def record_access(self, key: str) -> None:
        self._order.move_to_end(key)

    def record_remove(self, key: str) -> None:
        del self._order[key]

    def select_victim(self) -> str:
        return next(reversed(self._order))


def test_a_brand_new_strategy_plugs_in_without_changing_the_cache() -> None:
    cache = Cache[str, int](2, MruPolicy())
    cache.put("A", 1)
    cache.put("B", 1)
    cache.get("A")  # A is now the most recently used

    cache.put("C", 1)

    assert "A" not in cache  # MRU threw out the entry LRU would have kept
    assert "B" in cache
    assert "C" in cache


def test_the_context_does_not_care_which_strategy_it_holds() -> None:
    policies: list[EvictionPolicy[str]] = [MruPolicy(), LruPolicy()]
    for policy in policies:
        cache = Cache[str, int](2, policy)
        for key in "ABCD":
            cache.put(key, 1)
        assert len(cache) == 2


def test_sharing_one_policy_between_caches_breaks_it() -> None:
    """A policy's bookkeeping belongs to one cache. Build one policy per cache."""
    shared = LruPolicy[str]()
    first = Cache[str, int](2, shared)
    second = Cache[str, int](2, shared)
    first.put("a", 1)
    second.put("b", 1)
    second.put("c", 1)

    with pytest.raises(KeyError):  # the policy offers "a", which second never stored
        second.put("d", 1)
