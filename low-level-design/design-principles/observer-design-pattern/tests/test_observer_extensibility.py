from decimal import Decimal

from pricefeed import PriceFeed, PriceUpdate


class BigMoveDetector:
    """A new kind of observer, defined here, outside the library."""

    def __init__(self, threshold: Decimal) -> None:
        self.threshold = threshold
        self.moves: list[str] = []

    def __call__(self, update: PriceUpdate) -> None:
        if update.change is not None and abs(update.change) >= self.threshold:
            self.moves.append(f"{update.symbol} moved {update.change:+}")


class Recorder:
    def __init__(self) -> None:
        self.prices: list[Decimal] = []

    def on_price(self, update: PriceUpdate) -> None:  # a bound method as the observer
        self.prices.append(update.price)


def test_a_brand_new_observer_plugs_in_without_changing_the_feed() -> None:
    feed = PriceFeed()
    detector = BigMoveDetector(Decimal(5))
    feed.subscribe(detector)

    for price in ["100", "102", "110", "109"]:
        feed.publish("ACME", Decimal(price))

    assert detector.moves == ["ACME moved +8"]


def test_functions_lambdas_objects_and_bound_methods_all_work() -> None:
    feed = PriceFeed()
    from_function: list[str] = []
    recorder = Recorder()
    detector = BigMoveDetector(Decimal(1))

    def record_symbol(update: PriceUpdate) -> None:
        from_function.append(update.symbol)

    lambda_calls: list[Decimal] = []
    feed.subscribe(record_symbol)  # a function
    feed.subscribe(lambda update: lambda_calls.append(update.price))  # a lambda
    feed.subscribe(recorder.on_price)  # a bound method
    feed.subscribe(detector)  # an object with __call__

    feed.publish("ACME", Decimal(1))
    feed.publish("ACME", Decimal(5))

    assert from_function == ["ACME", "ACME"]
    assert lambda_calls == [Decimal(1), Decimal(5)]
    assert recorder.prices == [Decimal(1), Decimal(5)]
    assert detector.moves == ["ACME moved +4"]


def test_observers_do_not_know_about_each_other() -> None:
    feed = PriceFeed()
    first, second = Recorder(), Recorder()
    feed.subscribe(first.on_price)
    feed.subscribe(second.on_price)

    feed.publish("ACME", Decimal(1))

    assert first.prices == second.prices == [Decimal(1)]
