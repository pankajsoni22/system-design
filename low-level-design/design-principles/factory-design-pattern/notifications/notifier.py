from abc import ABC, abstractmethod
from collections.abc import Callable

from .channel import Channel, EmailChannel, PushChannel, SmsChannel
from .errors import InvalidNotification, TransientChannelError
from .gateway import ConsoleGateway, Gateway
from .result import DeliveryResult


class Notifier(ABC):
    """The creator: owns the delivery workflow, leaves *which channel* to subclasses."""

    max_attempts: int = 3

    def __init__(self, gateway: Gateway | None = None) -> None:
        self._gateway: Gateway = gateway or ConsoleGateway()

    @abstractmethod
    def create_channel(self) -> Channel:
        """The factory method: each subclass decides which channel to build."""

    def notify(self, recipient: str, message: str) -> DeliveryResult:
        channel = self.create_channel()  # the workflow never names a concrete class
        try:
            channel.validate(recipient, message)
        except InvalidNotification as problem:
            return DeliveryResult(False, channel.name, str(problem), attempts=0)

        detail = ""
        for attempt in range(1, self.max_attempts + 1):
            try:
                channel.deliver(recipient, message)
            except TransientChannelError as failure:
                detail = str(failure)
            else:
                return DeliveryResult(True, channel.name, "delivered", attempt)
        return DeliveryResult(
            False,
            channel.name,
            f"gave up after {self.max_attempts} attempts: {detail}",
            attempts=self.max_attempts,
        )


class EmailNotifier(Notifier):
    def create_channel(self) -> Channel:
        return EmailChannel(self._gateway)


class SmsNotifier(Notifier):
    max_attempts = 5  # example policy: a channel can carry its own retry budget

    def create_channel(self) -> Channel:
        return SmsChannel(self._gateway)


class PushNotifier(Notifier):
    max_attempts = 2

    def create_channel(self) -> Channel:
        return PushChannel(self._gateway)


class CallableNotifier(Notifier):
    """The Pythonic variant: pass the factory in, instead of writing a subclass."""

    def __init__(
        self,
        make_channel: Callable[[Gateway], Channel],
        gateway: Gateway | None = None,
        max_attempts: int = 3,
    ) -> None:
        super().__init__(gateway)
        self._make_channel = make_channel
        self.max_attempts = max_attempts

    def create_channel(self) -> Channel:
        return self._make_channel(self._gateway)
