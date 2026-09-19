from abc import ABC, abstractmethod
from typing import ClassVar


class Chair(ABC):
    style: ClassVar[str]

    @abstractmethod
    def describe(self) -> str: ...


class Sofa(ABC):
    style: ClassVar[str]

    @abstractmethod
    def describe(self) -> str: ...


class ModernChair(Chair):
    style = "modern"

    def describe(self) -> str:
        return "a slim metal chair"


class ModernSofa(Sofa):
    style = "modern"

    def describe(self) -> str:
        return "a low grey sofa"


class VictorianChair(Chair):
    style = "victorian"

    def describe(self) -> str:
        return "a carved wooden chair"


class VictorianSofa(Sofa):
    style = "victorian"

    def describe(self) -> str:
        return "a velvet sofa with curled arms"


class FurnitureFactory(ABC):
    """One factory per style. Each one builds a whole matching set."""

    @abstractmethod
    def create_chair(self) -> Chair: ...

    @abstractmethod
    def create_sofa(self) -> Sofa: ...


class ModernFactory(FurnitureFactory):
    def create_chair(self) -> Chair:
        return ModernChair()

    def create_sofa(self) -> Sofa:
        return ModernSofa()


class VictorianFactory(FurnitureFactory):
    def create_chair(self) -> Chair:
        return VictorianChair()

    def create_sofa(self) -> Sofa:
        return VictorianSofa()


class Showroom:
    """The code that uses the furniture. It never says which style it got."""

    def __init__(self, factory: FurnitureFactory) -> None:
        self._factory = factory

    def show(self) -> list[str]:
        chair = self._factory.create_chair()
        sofa = self._factory.create_sofa()
        return [f"Chair: {chair.describe()}", f"Sofa: {sofa.describe()}"]


if __name__ == "__main__":
    for name, factory in [
        ("Modern", ModernFactory()),
        ("Victorian", VictorianFactory()),
    ]:
        print(f"--- {name} showroom")
        for line in Showroom(factory).show():
            print(line)
