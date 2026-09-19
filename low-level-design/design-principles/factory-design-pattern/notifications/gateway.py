import sys
from typing import Protocol, TextIO


class Gateway(Protocol):
    """The outside world: an SMTP server, an SMS provider, a push service.

    Implementations raise `TransientChannelError` for failures worth retrying.
    """

    def send(self, address: str, text: str) -> None: ...


class ConsoleGateway:
    """Prints instead of sending. Handy for demos and local development."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream  # None means "current sys.stdout", looked up on use

    def send(self, address: str, text: str) -> None:
        print(f"to {address}: {text}", file=self._stream or sys.stdout)


class RecordingGateway:
    """Remembers everything it was asked to send. Handy for tests."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send(self, address: str, text: str) -> None:
        self.sent.append((address, text))
