from decimal import Decimal

from pricefeed import PriceFeed, PriceUpdate


def d(text: str) -> Decimal:
    return Decimal(text)


def test_an_observer_receives_each_update() -> None:
    feed = PriceFeed()
    seen: list[PriceUpdate] = []
    feed.subscribe(seen.append)

    feed.publish("ACME", d("10"))
    feed.publish("ACME", d("12"))

    assert [(u.symbol, u.price) for u in seen] == [("ACME", d("10")), ("ACME", d("12"))]


def test_every_observer_is_told_and_the_subject_knows_none_of_them() -> None:
    feed = PriceFeed()
    first: list[PriceUpdate] = []
    second: list[PriceUpdate] = []
    feed.subscribe(first.append)
    feed.subscribe(second.append)

    feed.publish("ACME", d("10"))

    assert len(first) == len(second) == 1


def test_a_symbol_filter_only_delivers_that_symbol() -> None:
    feed = PriceFeed()
    acme: list[PriceUpdate] = []
    everything: list[PriceUpdate] = []
    feed.subscribe(acme.append, symbol="ACME")
    feed.subscribe(everything.append)

    feed.publish("ACME", d("10"))
    feed.publish("GLOBEX", d("20"))

    assert [u.symbol for u in acme] == ["ACME"]
    assert [u.symbol for u in everything] == ["ACME", "GLOBEX"]


def test_observers_are_notified_in_subscription_order() -> None:
    feed = PriceFeed()
    order: list[str] = []
    feed.subscribe(lambda update: order.append("first"))
    feed.subscribe(lambda update: order.append("second"))
    feed.subscribe(lambda update: order.append("third"))

    feed.publish("ACME", d("1"))

    assert order == ["first", "second", "third"]


def test_publishing_with_no_observers_is_fine() -> None:
    feed = PriceFeed()
    feed.publish("ACME", d("1"))
    assert feed.latest("ACME") == d("1")


def test_updates_carry_the_previous_price_and_the_change() -> None:
    feed = PriceFeed()
    seen: list[PriceUpdate] = []
    feed.subscribe(seen.append)

    feed.publish("ACME", d("10"))
    feed.publish("ACME", d("12.5"))
    feed.publish("GLOBEX", d("7"))  # another symbol has its own history

    assert [u.previous for u in seen] == [None, d("10"), None]
    assert [u.change for u in seen] == [None, d("2.5"), None]


def test_latest_is_the_subjects_own_state() -> None:
    feed = PriceFeed()
    assert feed.latest("ACME") is None

    feed.publish("ACME", d("10"))
    feed.publish("ACME", d("11"))

    assert feed.latest("ACME") == d("11")


def test_the_same_callback_can_subscribe_twice() -> None:
    feed = PriceFeed()
    calls: list[int] = []

    def callback(update: PriceUpdate) -> None:
        calls.append(1)

    first = feed.subscribe(callback)
    feed.subscribe(callback)

    feed.publish("ACME", d("1"))
    assert len(calls) == 2  # two subscriptions, two deliveries

    first.cancel()  # each handle controls only its own subscription
    feed.publish("ACME", d("2"))
    assert len(calls) == 3
