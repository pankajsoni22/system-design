import threading
import time

import pytest

from logger import Logger


def test_get_instance_always_returns_the_same_object() -> None:
    assert Logger.get_instance() is Logger.get_instance()


def test_direct_construction_is_blocked() -> None:
    with pytest.raises(TypeError, match="get_instance"):
        Logger()


def test_many_threads_racing_to_create_build_exactly_one_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    thread_count = 32
    barrier = threading.Barrier(thread_count)  # release all threads at once
    real_build = Logger._build
    builds: list[int] = []

    def slow_build() -> Logger:
        builds.append(1)
        time.sleep(0.05)  # widen the race window so a missing lock cannot hide
        return real_build()

    monkeypatch.setattr(Logger, "_build", slow_build)
    seen: list[Logger] = []

    def worker() -> None:
        barrier.wait()
        seen.append(Logger.get_instance())

    threads = [threading.Thread(target=worker) for _ in range(thread_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(builds) == 1  # only one thread was allowed to build
    assert len({id(logger) for logger in seen}) == 1


def test_reset_gives_a_fresh_instance() -> None:
    first = Logger.get_instance()
    Logger._reset_for_testing()
    assert Logger.get_instance() is not first


def test_subclass_gets_base_instance_if_base_was_created_first() -> None:
    """A known trap of storing the instance in a class attribute."""

    class SubLogger(Logger):
        pass

    base = Logger.get_instance()
    assert SubLogger.get_instance() is base  # not a SubLogger at all
