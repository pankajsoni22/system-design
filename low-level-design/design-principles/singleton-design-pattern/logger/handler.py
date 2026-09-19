import sys
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TextIO

from .formatter import Formatter, SimpleFormatter
from .record import LogRecord


class LogHandler(ABC):
    """Decides *where* a record goes. Subclasses only implement `_emit`."""

    def __init__(self, formatter: Formatter | None = None) -> None:
        self._formatter: Formatter = formatter or SimpleFormatter()
        self._lock = threading.Lock()

    def handle(self, record: LogRecord) -> None:
        line = self._formatter.format(record)  # no lock needed to format
        with self._lock:  # one writer at a time, so lines never interleave
            self._emit(line)

    @abstractmethod
    def _emit(self, line: str) -> None: ...

    def close(self) -> None:
        """Release resources. Handlers that hold none can keep this default."""
        return


class ConsoleHandler(LogHandler):
    def __init__(
        self, stream: TextIO | None = None, formatter: Formatter | None = None
    ) -> None:
        super().__init__(formatter)
        self._stream = stream  # None means "current sys.stderr", looked up on use

    def _emit(self, line: str) -> None:
        print(line, file=self._stream or sys.stderr)


class FileHandler(LogHandler):
    def __init__(self, path: str | Path, formatter: Formatter | None = None) -> None:
        super().__init__(formatter)
        # kept open for the handler's lifetime and closed in close()
        self._file = Path(path).open("a", encoding="utf-8")  # noqa: SIM115

    def _emit(self, line: str) -> None:
        self._file.write(line + "\n")
        self._file.flush()  # a crash right after a log call must not lose the line

    def close(self) -> None:
        with self._lock:
            self._file.close()


class MemoryHandler(LogHandler):
    """Keeps lines in a list. Handy for tests, and a template for new handlers."""

    def __init__(self, formatter: Formatter | None = None) -> None:
        super().__init__(formatter)
        self.lines: list[str] = []

    def _emit(self, line: str) -> None:
        self.lines.append(line)
