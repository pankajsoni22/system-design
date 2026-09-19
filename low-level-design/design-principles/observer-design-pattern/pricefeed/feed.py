import logging
import weakref
from collections import deque
from collections.abc import Callable
from decimal import Decimal
from types import MethodType, TracebackType
from typing import Self

from .events import PriceUpdate

type Callback = Callable[[PriceUpdate], None]
type ErrorHandler = Callable[[Callback, Exception], None]

_log = logging.getLogger(__name__)


def _log_error(callback: Callback, error: Exception) -> None:
    _log.error("observer %r failed: %s", callback, error, exc_info=error)


def _strong_ref(callback: Callback) -> Callable[[], Callback | None]:
    def deref() -> Callback | None:
        return callback  # this reference keeps the observer alive

    return deref


def _weak_ref(callback: Callback) -> Callable[[], Callback | None]:
    if isinstance(callback, MethodType):  # a bound method: hold its object weakly
        return weakref.WeakMethod(callback)
    return weakref.ref(callback)


class Subscription:
    """The handle `subscribe` returns. Cancelling it stops all further deliveries."""

    def __init__(self, ref: Callable[[], Callback | None], symbol: str | None) -> None:
        self._ref = ref
        self.symbol = symbol
        self._cancelled = False

    def target(self) -> Callback | None:
        """The observer, or None if cancelled or (for weak ones) garbage collected."""
        return None if self._cancelled else self._ref()

    @property
    def active(self) -> bool:
        return self.target() is not None

    def cancel(self) -> None:
        self._cancelled = True  # safe to call twice, and safe mid-delivery

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.cancel()


class PriceFeed:
    """The subject: holds the latest prices and tells subscribers about each change.

    Delivery is synchronous, in subscription order. Not thread-safe.
    """

    def __init__(self, error_handler: ErrorHandler | None = None) -> None:
        self._subscriptions: list[Subscription] = []
        self._latest: dict[str, Decimal] = {}
        self._queue: deque[PriceUpdate] = deque()
        self._delivering = False
        self._on_error = error_handler or _log_error

    def subscribe(
        self, callback: Callback, symbol: str | None = None, *, weak: bool = False
    ) -> Subscription:
        """Register an observer for one symbol, or for all symbols if `symbol` is None.

        A weak subscription does not keep the observer alive. Someone else must hold it.
        """
        subscription = Subscription(
            _weak_ref(callback) if weak else _strong_ref(callback), symbol
        )
        self._subscriptions.append(subscription)
        return subscription

    def publish(self, symbol: str, price: Decimal) -> None:
        update = PriceUpdate(symbol, price, self._latest.get(symbol))
        self._latest[symbol] = price
        self._queue.append(update)
        if self._delivering:
            return  # called from inside an observer: wait until the current round ends
        self._delivering = True
        try:
            while self._queue:
                self._deliver(self._queue.popleft())
        finally:
            self._delivering = False

    def latest(self, symbol: str) -> Decimal | None:
        return self._latest.get(symbol)

    @property
    def observer_count(self) -> int:
        return sum(1 for subscription in self._subscriptions if subscription.active)

    def _deliver(self, update: PriceUpdate) -> None:
        self._subscriptions = [s for s in self._subscriptions if s.active]
        for subscription in list(self._subscriptions):  # a snapshot of this round
            if subscription.symbol not in (None, update.symbol):
                continue
            callback = subscription.target()  # None if cancelled during this round
            if callback is None:
                continue
            try:
                callback(update)
            except Exception as error:  # noqa: BLE001 - one bad observer must not stop the rest
                self._on_error(callback, error)
