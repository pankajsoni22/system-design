from collections.abc import Callable
from typing import Self

from .errors import UnknownChannelError
from .gateway import Gateway
from .notifier import EmailNotifier, Notifier, PushNotifier, SmsNotifier

NotifierCreator = Callable[[], Notifier]


class NotifierFactory:
    """A simple factory with a registry: channel name in, ready-to-use notifier out.

    Register everything at start-up. Afterwards it is only read, so it needs no lock.
    """

    def __init__(self) -> None:
        self._creators: dict[str, NotifierCreator] = {}

    def register(self, name: str, creator: NotifierCreator) -> None:
        if name in self._creators:
            raise ValueError(f"channel {name!r} is already registered")
        self._creators[name] = creator

    def create(self, name: str) -> Notifier:
        try:
            creator = self._creators[name]
        except KeyError:
            available = ", ".join(self.names) or "none"
            raise UnknownChannelError(
                f"unknown channel {name!r} (available: {available})"
            ) from None
        return creator()

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._creators))

    @classmethod
    def with_defaults(cls, gateway: Gateway | None = None) -> Self:
        factory = cls()
        factory.register("email", lambda: EmailNotifier(gateway))
        factory.register("sms", lambda: SmsNotifier(gateway))
        factory.register("push", lambda: PushNotifier(gateway))
        return factory
