"""No policy wins on every workload. These numbers appear in the tutorial."""

import pytest

from cache import Cache, make_policy

HOT_THEN_SCAN = list("AABBAB") + list("CDEFGH") + list("ABAB")
POPULAR_SET_CHANGES = list("XYXYXYXY") + list("PQR") * 4
FAVOURITE_AMONG_NEWCOMERS = list("ABC") + list("ADAEAFAGAHA")


def hits(policy_name: str, keys: list[str]) -> int:
    cache = Cache[str, int](3, make_policy(policy_name))
    for key in keys:
        if cache.get(key) is None:
            cache.put(key, 1)
    return cache.stats.hits


@pytest.mark.parametrize(
    ("keys", "expected_hits"),
    [
        (HOT_THEN_SCAN, {"fifo": 6, "lru": 6, "lfu": 8}),  # 16 lookups: LFU wins
        (POPULAR_SET_CHANGES, {"fifo": 15, "lru": 15, "lfu": 6}),  # 20: LFU loses
        (FAVOURITE_AMONG_NEWCOMERS, {"fifo": 4, "lru": 6, "lfu": 6}),  # 14: FIFO loses
    ],
)
def test_hits_per_policy_on_each_workload(
    keys: list[str], expected_hits: dict[str, int]
) -> None:
    assert {name: hits(name, keys) for name in expected_hits} == expected_hits
