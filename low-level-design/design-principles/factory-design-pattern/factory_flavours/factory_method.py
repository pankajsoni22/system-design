from abc import ABC, abstractmethod


class Vehicle(ABC):
    @abstractmethod
    def describe(self) -> str: ...


class AutoRickshaw(Vehicle):
    def describe(self) -> str:
        return "an auto-rickshaw"


class YellowCab(Vehicle):
    def describe(self) -> str:
        return "a yellow cab"


class RideApp(ABC):
    """Every city runs the same booking steps. Only the vehicle differs."""

    def book_ride(self, pickup: str, drop: str) -> list[str]:
        vehicle = self.create_vehicle()  # the factory method: the city decides
        return [
            f"Estimate the fare from {pickup} to {drop}",
            f"Send {vehicle.describe()} to {pickup}",
            "Track the trip",
            "Take the payment",
        ]

    @abstractmethod
    def create_vehicle(self) -> Vehicle:
        """Each city's app says which vehicle to create."""


class MumbaiRideApp(RideApp):
    def create_vehicle(self) -> Vehicle:
        return AutoRickshaw()


class NewYorkRideApp(RideApp):
    def create_vehicle(self) -> Vehicle:
        return YellowCab()


if __name__ == "__main__":
    for city, app in [("Mumbai", MumbaiRideApp()), ("New York", NewYorkRideApp())]:
        print(f"--- {city}")
        for step in app.book_ride("Central Station", "the airport"):
            print(step)
