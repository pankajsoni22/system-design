from dataclasses import dataclass
from datetime import datetime

from .level import LogLevel


@dataclass(frozen=True, slots=True)
class LogRecord:
    """One log event. Immutable, so it can be shared by every handler and thread."""

    timestamp: datetime
    level: LogLevel
    message: str
    thread_name: str
