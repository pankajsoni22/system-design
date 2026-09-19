from abc import ABC, abstractmethod


class Drink(ABC):
    """What every drink can do. The rest of the program only knows this much."""

    @abstractmethod
    def prepare(self) -> str: ...


class Espresso(Drink):
    def prepare(self) -> str:
        return "Pulling a shot of espresso"


class Latte(Drink):
    def prepare(self) -> str:
        return "Pulling a shot, steaming milk, pouring a latte"


class Tea(Drink):
    def prepare(self) -> str:
        return "Steeping a tea bag"


class DrinkFactory:
    """The simple factory: give it a name, get back the right drink."""

    def create(self, kind: str) -> Drink:
        if kind == "espresso":
            return Espresso()
        if kind == "latte":
            return Latte()
        if kind == "tea":
            return Tea()
        raise ValueError(f"we do not serve {kind!r}")


class Cafe:
    """The code that uses drinks. It never mentions Espresso, Latte or Tea."""

    def __init__(self, factory: DrinkFactory) -> None:
        self._factory = factory

    def order(self, kind: str) -> str:
        drink = self._factory.create(kind)
        return drink.prepare()


if __name__ == "__main__":
    cafe = Cafe(DrinkFactory())
    print(cafe.order("latte"))
    print(cafe.order("tea"))
    try:
        cafe.order("soup")
    except ValueError as problem:
        print(f"Sorry: {problem}")
