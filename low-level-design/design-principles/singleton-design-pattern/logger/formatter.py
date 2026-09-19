from typing import Protocol

from .record import LogRecord


class Formatter(Protocol):
    """Turns a record into a line of text. Any object with this method qualifies."""

    def format(self, record: LogRecord) -> str: ...


class SimpleFormatter:
    """Example: 2026-09-19T10:15:30.123+00:00 [INFO    ] [MainThread] message"""

    def format(self, record: LogRecord) -> str:
        timestamp = record.timestamp.isoformat(timespec="milliseconds")
        level = f"{record.level.name:<8}"
        return f"{timestamp} [{level}] [{record.thread_name}] {record.message}"
