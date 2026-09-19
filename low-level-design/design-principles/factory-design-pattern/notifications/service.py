from collections.abc import Mapping

from .errors import UnknownChannelError
from .factory import NotifierFactory
from .result import DeliveryResult


class NotificationService:
    """The client: knows channel *names* and the `Notifier` interface, nothing else."""

    def __init__(self, factory: NotifierFactory) -> None:
        self._factory = factory

    def send(self, channel: str, recipient: str, message: str) -> DeliveryResult:
        """Send on one channel. An unknown channel is a bug, so it raises."""
        return self._factory.create(channel).notify(recipient, message)

    def broadcast(
        self, addresses: Mapping[str, str], message: str
    ) -> list[DeliveryResult]:
        """Send on every channel a user has an address for, e.g. from saved preferences.

        Stored preferences can be stale, so an unknown channel becomes a failed
        result instead of stopping the channels that still work.
        """
        results: list[DeliveryResult] = []
        for channel, recipient in addresses.items():
            try:
                results.append(self.send(channel, recipient, message))
            except UnknownChannelError as problem:
                results.append(DeliveryResult(False, channel, str(problem), attempts=0))
        return results
