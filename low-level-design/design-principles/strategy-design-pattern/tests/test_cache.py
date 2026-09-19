import pytest

from cache import Cache, EvictionPolicy, FifoPolicy, LfuPolicy, LruPolicy


def test_get_returns_the_stored_value_or_the_default() -> None:
    cache = Cache[str, int](2, LruPolicy())
    cache.put("a", 0)  # a falsy value must still count as stored

    assert cache.get("a") == 0
    assert cache.get("missing") is None
    assert cache.get("missing", default=-1) == -1


def test_capacity_is_respected_and_evictions_are_counted() -> None:
    cache = Cache[str, int](3, LruPolicy())
    for key in "ABCD":
        cache.put(key, 1)

    assert len(cache) == 3
    assert cache.stats.evictions == 1


@pytest.mark.parametrize(
    ("policy_type", "expected_victim"),
    [(FifoPolicy, "A"), (LruPolicy, "B"), (LfuPolicy, "C")],
)
def test_the_same_history_gives_a_different_victim_per_policy(
    policy_type: type[EvictionPolicy[str]], expected_victim: str
) -> None:
    cache = Cache[str, int](3, policy_type())
    for key in "ABC":
        cache.put(key, 1)
    for key in "BBCA":  # counts: A=2, B=3, C=2. Recency, oldest first: B, C, A
        cache.get(key)

    cache.put("D", 1)

    assert [key for key in "ABC" if key not in cache] == [expected_victim]


def test_overwriting_replaces_the_value_without_growing() -> None:
    cache = Cache[str, int](2, LruPolicy())
    cache.put("a", 1)
    cache.put("a", 2)

    assert len(cache) == 1
    assert cache.get("a") == 2


def test_overwriting_restarts_the_history_of_that_key() -> None:
    cache = Cache[str, int](2, LfuPolicy())
    cache.put("A", 1)
    cache.put("B", 1)
    cache.get("A")
    cache.get("A")  # A has been read a lot
    cache.get("B")
    cache.put("A", 2)  # overwritten: A starts again from a count of 1

    cache.put("C", 1)

    assert "A" not in cache
    assert "B" in cache


def test_delete_removes_the_entry_and_frees_its_space() -> None:
    cache = Cache[str, int](2, LruPolicy())
    cache.put("a", 1)
    cache.put("b", 1)

    assert cache.delete("a") is True
    assert cache.delete("a") is False

    cache.put("c", 1)  # there was room, so nothing is evicted
    assert cache.stats.evictions == 0
    assert len(cache) == 2


def test_the_in_operator_is_a_peek_not_a_read() -> None:
    cache = Cache[str, int](2, LruPolicy())
    cache.put("A", 1)
    cache.put("B", 1)

    assert "A" in cache  # must not refresh A
    cache.put("C", 1)

    assert "A" not in cache
    assert cache.stats.hits == 0
    assert cache.stats.misses == 0


def test_stats_and_hit_rate() -> None:
    cache = Cache[str, int](2, LruPolicy())
    assert cache.stats.hit_rate == 0.0  # no lookups yet

    cache.put("a", 1)
    cache.get("a")
    cache.get("a")
    cache.get("nope")

    stats = cache.stats
    assert (stats.hits, stats.misses) == (2, 1)
    assert stats.hit_rate == pytest.approx(2 / 3)


def test_the_injected_policy_is_the_one_in_use() -> None:
    policy = LruPolicy[str]()
    assert Cache[str, int](1, policy).policy is policy


def test_cache_talks_to_its_policy_only_through_the_interface() -> None:
    """A spy shows the exact conversation between the context and the strategy."""
    calls: list[str] = []

    class SpyPolicy(LruPolicy[str]):
        def record_insert(self, key: str) -> None:
            calls.append(f"insert {key}")
            super().record_insert(key)

        def record_access(self, key: str) -> None:
            calls.append(f"access {key}")
            super().record_access(key)

        def record_remove(self, key: str) -> None:
            calls.append(f"remove {key}")
            super().record_remove(key)

        def select_victim(self) -> str:
            calls.append("victim")
            return super().select_victim()

    cache = Cache[str, int](2, SpyPolicy())
    cache.put("A", 1)
    cache.put("B", 1)
    cache.get("A")
    cache.get("Z")  # a miss tells the policy nothing
    cache.put("C", 1)  # full: ask for a victim, remove it, then insert
    cache.put("A", 2)  # overwrite: remove the old entry, insert the new one
    cache.delete("C")

    assert calls == [
        "insert A",
        "insert B",
        "access A",
        "victim",
        "remove B",
        "insert C",
        "remove A",
        "insert A",
        "remove C",
    ]


def test_the_weigher_decides_what_capacity_means() -> None:
    cache = Cache[str, str](10, LruPolicy(), weigher=lambda key, text: len(text))
    cache.put("a", "hello")  # 5
    cache.put("b", "world")  # 5, now full
    cache.put("c", "hi")  # 2, so the least recently used entry goes

    assert [key for key in "abc" if key in cache] == ["b", "c"]
    assert cache.used == 7


def test_one_heavy_entry_can_evict_several_light_ones() -> None:
    cache = Cache[str, str](10, LruPolicy(), weigher=lambda key, text: len(text))
    cache.put("a", "12345")
    cache.put("b", "123")
    cache.put("c", "12")

    cache.put("d", "123456789")  # weighs 9: needs a, b and c all gone

    assert [key for key in "abcd" if key in cache] == ["d"]
    assert cache.stats.evictions == 3
    assert cache.used == 9


def test_an_entry_heavier_than_the_whole_cache_is_rejected() -> None:
    cache = Cache[str, str](5, LruPolicy(), weigher=lambda key, text: len(text))
    cache.put("a", "abc")

    with pytest.raises(ValueError, match="more than the capacity"):
        cache.put("b", "too long for this cache")

    assert "a" in cache  # nothing was evicted for a doomed insert
    assert cache.used == 3


def test_weights_below_one_are_rejected() -> None:
    cache = Cache[str, str](5, LruPolicy(), weigher=lambda key, text: len(text))
    with pytest.raises(ValueError, match="at least 1"):
        cache.put("empty", "")


def test_capacity_must_be_positive() -> None:
    with pytest.raises(ValueError, match="capacity"):
        Cache[str, int](0, LruPolicy())


def test_the_strategy_can_be_swapped_at_run_time() -> None:
    cache = Cache[str, int](3, LruPolicy())
    for key in "ABC":
        cache.put(key, 1)
    cache.get("A")  # LRU would now evict B

    cache.set_policy(FifoPolicy())  # FIFO restarts in storage order: A, B, C
    cache.put("D", 1)

    assert [key for key in "ABC" if key not in cache] == ["A"]
    assert isinstance(cache.policy, FifoPolicy)
