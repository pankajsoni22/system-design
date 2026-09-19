import pytest

from cache import (
    Cache,
    FifoPolicy,
    LfuPolicy,
    LruPolicy,
    UnknownPolicyError,
    make_policy,
)


@pytest.mark.parametrize(
    ("name", "policy_type"),
    [("fifo", FifoPolicy), ("lru", LruPolicy), ("lfu", LfuPolicy)],
)
def test_names_map_to_policies(name: str, policy_type: type) -> None:
    assert type(make_policy(name)) is policy_type


def test_every_call_builds_a_fresh_policy() -> None:
    assert make_policy("lru") is not make_policy("lru")


def test_unknown_name_lists_the_valid_ones() -> None:
    with pytest.raises(UnknownPolicyError) as error:
        make_policy("mru")

    assert "'mru'" in str(error.value)
    assert "fifo, lfu, lru" in str(error.value)


def test_a_policy_built_from_a_name_plugs_into_a_cache() -> None:
    cache = Cache[str, int](1, make_policy("lru"))
    cache.put("a", 1)
    cache.put("b", 2)

    assert "a" not in cache
    assert cache.get("b") == 2
