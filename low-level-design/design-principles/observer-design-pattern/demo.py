import gc
import weakref
from decimal import Decimal

from pricefeed import (
    MovingAverage,
    PriceFeed,
    PriceUpdate,
    ThresholdAlert,
    print_update,
)


def price_alerts() -> None:
    feed = PriceFeed()
    alert = ThresholdAlert("ACME", above=Decimal(100))
    average = MovingAverage("ACME", window=3)
    feed.subscribe(alert, symbol="ACME")
    feed.subscribe(average, symbol="ACME")
    feed.subscribe(print_update)  # a plain function that sees every symbol

    for price in ["98", "101", "103", "99", "102"]:
        feed.publish("ACME", Decimal(price))
    feed.publish("GLOBEX", Decimal("55.50"))
    print(f"average of the last 3 ACME prices: {average.value:.2f}")


def scoped_subscription() -> None:
    feed = PriceFeed()
    with feed.subscribe(print_update):  # cancelled automatically when the block ends
        feed.publish("ACME", Decimal(1))
    feed.publish("ACME", Decimal(2))  # nobody is listening any more
    print(f"observers left: {feed.observer_count}")


def one_bad_observer() -> None:
    errors: list[str] = []
    seen: list[str] = []

    def fail(update: PriceUpdate) -> None:
        raise RuntimeError("boom")

    feed = PriceFeed(error_handler=lambda callback, error: errors.append(str(error)))
    feed.subscribe(fail)
    feed.subscribe(lambda update: seen.append(update.symbol))
    feed.publish("ACME", Decimal(1))
    print(f"one observer failed ({errors[0]}), the other still ran: {seen}")


class Dashboard:
    def on_price(self, update: PriceUpdate) -> None:
        pass


def forgotten_observer() -> None:
    strong_feed, weak_feed = PriceFeed(), PriceFeed()
    strong_dashboard, weak_dashboard = Dashboard(), Dashboard()
    strong_ref = weakref.ref(strong_dashboard)
    weak_ref = weakref.ref(weak_dashboard)
    strong_feed.subscribe(strong_dashboard.on_price)
    weak_feed.subscribe(weak_dashboard.on_price, weak=True)

    del strong_dashboard, weak_dashboard  # the program forgets both dashboards
    gc.collect()
    print(
        f"strong subscription still keeps its dashboard alive: {strong_ref() is not None}"
    )
    print(f"weak subscription let its dashboard go: {weak_ref() is None}")
    weak_feed.publish("ACME", Decimal(1))  # prunes the dead subscription
    print(f"observers left on the weak feed: {weak_feed.observer_count}")


if __name__ == "__main__":
    price_alerts()
    scoped_subscription()
    one_bad_observer()
    forgotten_observer()
