import re
from abc import ABC, abstractmethod
from typing import ClassVar

from .errors import InvalidNotification
from .gateway import Gateway


class Channel(ABC):
    """The product: one way of reaching a person, with its own rules."""

    name: ClassVar[str]

    def __init__(self, gateway: Gateway) -> None:
        self._gateway = gateway

    @abstractmethod
    def validate(self, recipient: str, message: str) -> None:
        """Raise `InvalidNotification` if this channel cannot deliver this."""

    @abstractmethod
    def deliver(self, recipient: str, message: str) -> None:
        """Hand the message to the gateway. May raise `TransientChannelError`."""


class EmailChannel(Channel):
    name = "email"
    _ADDRESS: ClassVar[re.Pattern[str]] = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

    def validate(self, recipient: str, message: str) -> None:
        if not self._ADDRESS.fullmatch(recipient):
            raise InvalidNotification(f"not an email address: {recipient!r}")
        if not message.strip():
            raise InvalidNotification("email body is empty")

    def deliver(self, recipient: str, message: str) -> None:
        self._gateway.send(recipient, f"[email] Subject: Notification | {message}")


class SmsChannel(Channel):
    name = "sms"
    MAX_LENGTH: ClassVar[int] = 160  # the classic single-message limit
    _NUMBER: ClassVar[re.Pattern[str]] = re.compile(r"\+[1-9]\d{7,14}")  # E.164

    def validate(self, recipient: str, message: str) -> None:
        if not self._NUMBER.fullmatch(recipient):
            raise InvalidNotification(f"not an E.164 phone number: {recipient!r}")
        if not message.strip():
            raise InvalidNotification("sms text is empty")
        if len(message) > self.MAX_LENGTH:
            raise InvalidNotification(
                f"sms text is {len(message)} characters, the limit is {self.MAX_LENGTH}"
            )

    def deliver(self, recipient: str, message: str) -> None:
        self._gateway.send(recipient, f"[sms] {message}")


class PushChannel(Channel):
    name = "push"
    MAX_LENGTH: ClassVar[int] = 200  # illustrative limit for this tutorial
    _TOKEN: ClassVar[re.Pattern[str]] = re.compile(r"[A-Za-z0-9_-]{8,}")

    def validate(self, recipient: str, message: str) -> None:
        if not self._TOKEN.fullmatch(recipient):
            raise InvalidNotification(f"not a device token: {recipient!r}")
        if not message.strip():
            raise InvalidNotification("push text is empty")
        if len(message) > self.MAX_LENGTH:
            raise InvalidNotification(
                f"push text is {len(message)} characters, the limit is {self.MAX_LENGTH}"
            )

    def deliver(self, recipient: str, message: str) -> None:
        self._gateway.send(recipient, f"[push] {message}")
