from decimal import Decimal

import pytest

from pricefeed import MovingAverage, PriceUpdate, ThresholdAlert, print_update


def update(
    price: str, symbol: str = "ACME", previous: str | None = None
) -> PriceUpdate:
    return PriceUpdate(
        symbol, Decimal(price), None if previous is None else Decimal(previous)
    )


def test_alert_fires_once_when_the_price_crosses_above_the_level() -> None:
    alerts: list[str] = []
    alert = ThresholdAlert("ACME", above=Decimal(100), notify=alerts.append)

    for price in ["98", "101", "103", "105"]:
        alert(update(price))

    assert alerts == ["ALERT ACME rose above 100: 101"]  # not again at 103 or 105


def test_alert_rearms_after_the_price_falls_back() -> None:
    alerts: list[str] = []
    alert = ThresholdAlert("ACME", above=Decimal(100), notify=alerts.append)

    for price in ["101", "99", "102"]:
        alert(update(price))

    assert len(alerts) == 2


def test_a_price_exactly_at_the_level_is_not_above_it() -> None:
    alerts: list[str] = []
    alert = ThresholdAlert("ACME", above=Decimal(100), notify=alerts.append)

    alert(update("100"))

    assert alerts == []


def test_alert_ignores_other_symbols_even_if_subscribed_to_everything() -> None:
    alerts: list[str] = []
    alert = ThresholdAlert("ACME", above=Decimal(100), notify=alerts.append)

    alert(update("500", symbol="GLOBEX"))

    assert alerts == []


def test_moving_average_uses_only_the_last_window_prices() -> None:
    average = MovingAverage("ACME", window=3)
    assert average.value is None

    for price in ["10", "20", "30", "40"]:
        average(update(price))

    assert average.value == Decimal(30)  # (20 + 30 + 40) / 3


def test_moving_average_ignores_other_symbols() -> None:
    average = MovingAverage("ACME", window=3)
    average(update("10"))
    average(update("999", symbol="GLOBEX"))

    assert average.value == Decimal(10)


def test_moving_average_needs_a_positive_window() -> None:
    with pytest.raises(ValueError, match="window"):
        MovingAverage("ACME", window=0)


def test_print_update_shows_the_change(capsys: pytest.CaptureFixture[str]) -> None:
    print_update(update("103", previous="101"))
    print_update(update("55.50", symbol="GLOBEX"))

    assert capsys.readouterr().out.splitlines() == [
        "ACME 103 (+2)",
        "GLOBEX 55.50 (first price)",
    ]
