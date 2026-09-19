from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PriceUpdate:
    """What observers receive: the new price, and the price it replaced."""

    symbol: str
    price: Decimal
    previous: Decimal | None

    @property
    def change(self) -> Decimal | None:
        return None if self.previous is None else self.price - self.previous
