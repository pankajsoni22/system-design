from collections import deque
from collections.abc import Callable
from decimal import Decimal

from .events import PriceUpdate


def print_update(update: PriceUpdate) -> None:
    """A stateless observer is just a function."""
    change = "first price" if update.change is None else f"{update.change:+}"
    print(f"{update.symbol} {update.price} ({change})")


class ThresholdAlert:
    """Fires once each time the price rises from at-or-below the level to above it."""

    def __init__(
        self,
        symbol: str,
        above: Decimal,
        notify: Callable[[str], None] = print,
    ) -> None:
        self._symbol = symbol
        self._above = above
        self._notify = notify
        self._is_above = False  # the state that makes this observer a class

    def __call__(self, update: PriceUpdate) -> None:
        if update.symbol != self._symbol:
            return
        now_above = update.price > self._above
        if now_above and not self._is_above:
            self._notify(
                f"ALERT {self._symbol} rose above {self._above}: {update.price}"
            )
        self._is_above = now_above


class MovingAverage:
    """The average of the last `window` prices of one symbol."""

    def __init__(self, symbol: str, window: int) -> None:
        if window < 1:
            raise ValueError("window must be at least 1")
        self._symbol = symbol
        self._prices: deque[Decimal] = deque(maxlen=window)

    def __call__(self, update: PriceUpdate) -> None:
        if update.symbol == self._symbol:
            self._prices.append(update.price)

    @property
    def value(self) -> Decimal | None:
        if not self._prices:
            return None
        return sum(self._prices, Decimal(0)) / len(self._prices)
