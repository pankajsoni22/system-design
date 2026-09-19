from decimal import Decimal

import pytest

from pricefeed import Callback, PriceFeed, PriceUpdate, Subscription


def d(text: str) -> Decimal:
    return Decimal(text)


def test_cancel_stops_deliveries_and_is_idempotent() -> None:
    feed = PriceFeed()
    seen: list[PriceUpdate] = []
    subscription = feed.subscribe(seen.append)

    feed.publish("ACME", d("1"))
    subscription.cancel()
    subscription.cancel()  # a second cancel is harmless
    feed.publish("ACME", d("2"))

    assert len(seen) == 1
    assert subscription.active is False
    assert feed.observer_count == 0


def test_a_with_block_cancels_on_exit() -> None:
    feed = PriceFeed()
    seen: list[PriceUpdate] = []

    with feed.subscribe(seen.append):
        feed.publish("ACME", d("1"))
    feed.publish("ACME", d("2"))

    assert len(seen) == 1


def test_an_observer_cancelled_mid_round_is_skipped_in_that_round() -> None:
    feed = PriceFeed()
    calls: list[str] = []
    victims: list[Subscription] = []

    def assassin(update: PriceUpdate) -> None:
        calls.append("assassin")
        victims[0].cancel()

    feed.subscribe(assassin)
    victims.append(feed.subscribe(lambda update: calls.append("victim")))

    feed.publish("ACME", d("1"))

    assert calls == ["assassin"]  # the victim never ran, even though it came later


def test_an_observer_added_mid_round_starts_with_the_next_update() -> None:
    feed = PriceFeed()
    late: list[PriceUpdate] = []

    def recruiter(update: PriceUpdate) -> None:
        if not late:
            feed.subscribe(late.append)

    feed.subscribe(recruiter)

    feed.publish("ACME", d("1"))
    assert late == []  # not part of the round that created it

    feed.publish("ACME", d("2"))
    assert [u.price for u in late] == [d("2")]


def test_a_failing_observer_does_not_stop_the_others() -> None:
    errors: list[tuple[Callback, Exception]] = []
    feed = PriceFeed(
        error_handler=lambda callback, error: errors.append((callback, error))
    )
    seen: list[PriceUpdate] = []

    def broken(update: PriceUpdate) -> None:
        raise RuntimeError("boom")

    feed.subscribe(seen.append)  # before the broken one
    feed.subscribe(broken)
    feed.subscribe(seen.append)  # after the broken one

    feed.publish("ACME", d("1"))

    assert len(seen) == 2
    assert len(errors) == 1
    assert errors[0][0] is broken
    assert str(errors[0][1]) == "boom"


def test_the_default_error_handler_logs_and_carries_on(
    caplog: pytest.LogCaptureFixture,
) -> None:
    feed = PriceFeed()
    seen: list[PriceUpdate] = []

    def broken(update: PriceUpdate) -> None:
        raise RuntimeError("boom")

    feed.subscribe(broken)
    feed.subscribe(seen.append)

    with caplog.at_level("ERROR"):
        feed.publish("ACME", d("1"))

    assert len(seen) == 1
    assert "failed: boom" in caplog.text


def test_a_publish_from_inside_an_observer_keeps_one_order_for_all() -> None:
    """Without queueing, the second observer would see the nested update first."""
    feed = PriceFeed()
    first_saw: list[str] = []
    second_saw: list[str] = []

    def first(update: PriceUpdate) -> None:
        first_saw.append(update.symbol)
        if update.symbol == "A":
            feed.publish("B", d("2"))  # a reaction that publishes another update

    def second(update: PriceUpdate) -> None:
        second_saw.append(update.symbol)

    feed.subscribe(first)
    feed.subscribe(second)

    feed.publish("A", d("1"))

    assert first_saw == ["A", "B"]
    assert second_saw == ["A", "B"]


def test_the_feed_recovers_after_a_publish_from_inside_an_observer() -> None:
    feed = PriceFeed()
    seen: list[str] = []

    def echo(update: PriceUpdate) -> None:
        seen.append(update.symbol)
        if update.symbol == "A":
            feed.publish("B", d("2"))

    feed.subscribe(echo)
    feed.publish("A", d("1"))
    feed.publish("C", d("3"))  # a normal publish afterwards still delivers

    assert seen == ["A", "B", "C"]


def test_dead_subscriptions_are_dropped_from_the_feeds_list() -> None:
    """Housekeeping: cancelled subscriptions must not pile up forever."""
    feed = PriceFeed()
    for _ in range(3):
        feed.subscribe(lambda update: None).cancel()
    keep = feed.subscribe(lambda update: None)

    feed.publish("ACME", d("1"))

    assert feed._subscriptions == [keep]
