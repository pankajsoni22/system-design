import gc
import weakref
from decimal import Decimal

from pricefeed import PriceFeed, PriceUpdate


class Listener:
    def __init__(self) -> None:
        self.seen: list[PriceUpdate] = []

    def on_price(self, update: PriceUpdate) -> None:
        self.seen.append(update)


def test_a_strong_subscription_keeps_the_observer_alive() -> None:
    """The lapsed listener problem: forgetting to unsubscribe leaks the observer."""
    feed = PriceFeed()
    listener = Listener()
    ref = weakref.ref(listener)
    feed.subscribe(listener.on_price)

    del listener
    gc.collect()

    assert ref() is not None  # the feed is still holding it
    assert feed.observer_count == 1


def test_a_weak_subscription_lets_the_observer_be_collected() -> None:
    feed = PriceFeed()
    listener = Listener()
    ref = weakref.ref(listener)
    feed.subscribe(listener.on_price, weak=True)

    del listener
    gc.collect()

    assert ref() is None
    assert feed.observer_count == 0


def test_a_collected_weak_observer_is_never_called_and_is_pruned() -> None:
    feed = PriceFeed()
    listener = Listener()
    feed.subscribe(listener.on_price, weak=True)
    survivor: list[PriceUpdate] = []
    feed.subscribe(survivor.append)

    del listener
    gc.collect()
    feed.publish("ACME", Decimal(1))  # must not raise

    assert len(survivor) == 1
    assert feed.observer_count == 1


def test_a_weak_subscription_still_delivers_while_the_observer_lives() -> None:
    feed = PriceFeed()
    listener = Listener()
    feed.subscribe(listener.on_price, weak=True)

    feed.publish("ACME", Decimal(1))

    assert len(listener.seen) == 1


def test_a_weak_lambda_vanishes_at_once_because_nothing_else_holds_it() -> None:
    """A pitfall worth knowing: weak means someone else must own the observer."""
    feed = PriceFeed()
    calls: list[PriceUpdate] = []
    feed.subscribe(lambda update: calls.append(update), weak=True)
    gc.collect()

    feed.publish("ACME", Decimal(1))

    assert calls == []
    assert feed.observer_count == 0
