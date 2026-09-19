"""Tests for the three small teaching examples in `factory_flavours/`."""

from typing import ClassVar

import pytest

from factory_flavours.abstract_factory import (
    Chair,
    FurnitureFactory,
    ModernFactory,
    Showroom,
    Sofa,
    VictorianFactory,
)
from factory_flavours.factory_method import (
    AutoRickshaw,
    MumbaiRideApp,
    NewYorkRideApp,
    RideApp,
    Vehicle,
    YellowCab,
)
from factory_flavours.simple_factory import (
    Cafe,
    Drink,
    DrinkFactory,
    Espresso,
    Latte,
    Tea,
)

# ---------------------------------------------------------------- Simple Factory


@pytest.mark.parametrize(
    ("kind", "expected"),
    [("espresso", Espresso), ("latte", Latte), ("tea", Tea)],
)
def test_the_simple_factory_builds_the_drink_that_was_asked_for(
    kind: str, expected: type[Drink]
) -> None:
    assert type(DrinkFactory().create(kind)) is expected


def test_the_simple_factory_refuses_a_drink_it_does_not_know() -> None:
    with pytest.raises(ValueError, match="soup"):
        DrinkFactory().create("soup")


def test_every_order_gets_a_new_drink_object() -> None:
    factory = DrinkFactory()
    assert factory.create("tea") is not factory.create("tea")


def test_the_cafe_only_talks_to_the_factory() -> None:
    """The code that uses drinks can be tested with a fake factory."""

    class StubDrink(Drink):
        def prepare(self) -> str:
            return "a stub drink"

    class FakeFactory(DrinkFactory):
        def create(self, kind: str) -> Drink:
            return StubDrink()

    assert Cafe(FakeFactory()).order("anything at all") == "a stub drink"


def test_the_cafe_serves_real_drinks() -> None:
    assert Cafe(DrinkFactory()).order("tea") == "Steeping a tea bag"


# --------------------------------------------------------------- Factory Method


def test_each_city_sends_its_own_vehicle() -> None:
    mumbai = MumbaiRideApp().book_ride("A", "B")
    new_york = NewYorkRideApp().book_ride("A", "B")

    assert "an auto-rickshaw" in mumbai[1]
    assert "a yellow cab" in new_york[1]


def test_the_booking_steps_are_the_same_in_every_city() -> None:
    mumbai = MumbaiRideApp().book_ride("A", "B")
    new_york = NewYorkRideApp().book_ride("A", "B")

    def without_the_vehicle_line(steps: list[str]) -> list[str]:
        return [steps[0], *steps[2:]]

    assert len(mumbai) == len(new_york) == 4
    assert without_the_vehicle_line(mumbai) == without_the_vehicle_line(new_york)


def test_the_factory_method_is_called_once_per_booking() -> None:
    class CountingApp(MumbaiRideApp):
        created = 0

        def create_vehicle(self) -> Vehicle:
            self.created += 1
            return super().create_vehicle()

    app = CountingApp()
    app.book_ride("A", "B")
    app.book_ride("A", "B")

    assert app.created == 2


def test_a_new_city_needs_only_a_new_subclass() -> None:
    class TukTuk(Vehicle):
        def describe(self) -> str:
            return "a tuk-tuk"

    class BangkokRideApp(RideApp):
        def create_vehicle(self) -> Vehicle:
            return TukTuk()

    steps = BangkokRideApp().book_ride("A", "B")  # RideApp itself was not touched

    assert "a tuk-tuk" in steps[1]
    assert len(steps) == 4


def test_the_base_app_cannot_be_used_on_its_own() -> None:
    with pytest.raises(TypeError, match="abstract"):
        RideApp()  # type: ignore[abstract]


def test_vehicles_describe_themselves() -> None:
    assert AutoRickshaw().describe() == "an auto-rickshaw"
    assert YellowCab().describe() == "a yellow cab"


# ------------------------------------------------------------- Abstract Factory


@pytest.mark.parametrize(
    ("factory", "style"),
    [(ModernFactory(), "modern"), (VictorianFactory(), "victorian")],
)
def test_everything_from_one_factory_matches(
    factory: FurnitureFactory, style: str
) -> None:
    assert factory.create_chair().style == style
    assert factory.create_sofa().style == style


def test_the_two_families_really_are_different() -> None:
    assert (
        ModernFactory().create_chair().describe()
        != VictorianFactory().create_chair().describe()
    )


def test_the_showroom_shows_whichever_family_it_was_given() -> None:
    assert Showroom(ModernFactory()).show() == [
        "Chair: a slim metal chair",
        "Sofa: a low grey sofa",
    ]
    assert Showroom(VictorianFactory()).show() == [
        "Chair: a carved wooden chair",
        "Sofa: a velvet sofa with curled arms",
    ]


def test_a_new_family_works_with_the_showroom_unchanged() -> None:
    class ScandiChair(Chair):
        style: ClassVar[str] = "scandinavian"

        def describe(self) -> str:
            return "a pale birch chair"

    class ScandiSofa(Sofa):
        style: ClassVar[str] = "scandinavian"

        def describe(self) -> str:
            return "a woollen two-seater"

    class ScandiFactory(FurnitureFactory):
        def create_chair(self) -> Chair:
            return ScandiChair()

        def create_sofa(self) -> Sofa:
            return ScandiSofa()

    assert Showroom(ScandiFactory()).show() == [
        "Chair: a pale birch chair",
        "Sofa: a woollen two-seater",
    ]


def test_a_factory_must_make_every_kind_of_product() -> None:
    """The rigid side of Abstract Factory: a half-finished family is refused."""

    class HalfFactory(FurnitureFactory):
        def create_chair(self) -> Chair:
            return ModernFactory().create_chair()

    with pytest.raises(TypeError, match="create_sofa"):
        HalfFactory()  # type: ignore[abstract]
