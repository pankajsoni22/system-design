import pytest

from cache import EvictionPolicy, FifoPolicy, LfuPolicy, LruPolicy


def test_lru_evicts_the_least_recently_used_key() -> None:
    policy = LruPolicy[str]()
    for key in "abc":
        policy.record_insert(key)

    policy.record_access("a")  # order is now b, c, a
    assert policy.select_victim() == "b"

    policy.record_remove("b")
    assert policy.select_victim() == "c"


def test_fifo_ignores_reads() -> None:
    policy = FifoPolicy[str]()
    for key in "abc":
        policy.record_insert(key)

    policy.record_access("a")
    policy.record_access("a")

    assert policy.select_victim() == "a"  # still the oldest, however popular
    policy.record_remove("a")
    assert policy.select_victim() == "b"


def test_lfu_evicts_the_least_frequently_used_key() -> None:
    policy = LfuPolicy[str]()
    for key in "abc":
        policy.record_insert(key)
    policy.record_access("a")
    policy.record_access("a")
    policy.record_access("b")  # counts: a=3, b=2, c=1

    assert policy.select_victim() == "c"
    policy.record_remove("c")
    assert policy.select_victim() == "b"
    policy.record_remove("b")
    assert policy.select_victim() == "a"


def test_lfu_breaks_ties_by_who_waited_longest_at_that_count() -> None:
    policy = LfuPolicy[str]()
    policy.record_insert("x")
    policy.record_insert("y")
    policy.record_access("x")  # x reaches count 2 first
    policy.record_access("y")  # y reaches count 2 second

    assert policy.select_victim() == "x"


def test_lfu_keeps_working_after_a_whole_count_bucket_empties() -> None:
    policy = LfuPolicy[str]()
    policy.record_insert("a")
    policy.record_insert("b")
    policy.record_access("a")  # bucket 1 now holds only b
    policy.record_remove("b")  # bucket 1 is gone entirely

    assert policy.select_victim() == "a"


@pytest.mark.parametrize("policy_type", [FifoPolicy, LruPolicy, LfuPolicy])
def test_an_empty_policy_has_no_victim(policy_type: type[EvictionPolicy[str]]) -> None:
    with pytest.raises(LookupError, match="no entries"):
        policy_type().select_victim()


def test_the_interface_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        EvictionPolicy()  # type: ignore[abstract]


def test_a_policy_missing_a_method_is_rejected_when_created() -> None:
    class Incomplete(EvictionPolicy[str]):
        def record_insert(self, key: str) -> None:
            return

    with pytest.raises(TypeError, match="abstract"):
        Incomplete()  # type: ignore[abstract]
