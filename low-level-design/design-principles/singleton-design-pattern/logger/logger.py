import sys
import threading
from datetime import UTC, datetime
from typing import Self

from .handler import LogHandler
from .level import LogLevel
from .record import LogRecord


class Logger:
    """The one application-wide logger. Get it with `Logger.get_instance()`."""

    _instance: Self | None = None
    _instance_lock = threading.Lock()

    _level: LogLevel
    _handlers: tuple[LogHandler, ...]
    _config_lock: threading.Lock

    def __init__(self) -> None:
        raise TypeError("Logger is a singleton: use Logger.get_instance()")

    @classmethod
    def get_instance(cls) -> Self:
        if cls._instance is None:  # 1st check: no lock on the common path
            with cls._instance_lock:
                if cls._instance is None:  # 2nd check: another thread may have won
                    cls._instance = cls._build()  # publish only when fully built
        return cls._instance

    @classmethod
    def _build(cls) -> Self:
        instance = object.__new__(cls)  # skips __init__, so the guard is not hit
        instance._level = LogLevel.INFO
        instance._handlers = ()
        instance._config_lock = threading.Lock()
        return instance

    # ---- configuration -------------------------------------------------

    @property
    def handlers(self) -> tuple[LogHandler, ...]:
        return self._handlers

    def set_level(self, level: LogLevel) -> None:
        self._level = level

    def add_handler(self, handler: LogHandler) -> None:
        with self._config_lock:
            # copy-on-write: log() can iterate the old tuple without a lock
            self._handlers = (*self._handlers, handler)

    def shutdown(self) -> None:
        with self._config_lock:
            handlers, self._handlers = self._handlers, ()
        for handler in handlers:
            handler.close()

    # ---- logging -------------------------------------------------------

    def log(self, level: LogLevel, message: str) -> None:
        if level < self._level:  # cheapest possible exit for filtered messages
            return
        record = LogRecord(
            timestamp=datetime.now(UTC),
            level=level,
            message=message,
            thread_name=threading.current_thread().name,
        )
        for handler in self._handlers:
            try:
                handler.handle(record)
            except Exception as exc:  # noqa: BLE001 - logging must never crash the app
                name = type(handler).__name__
                print(f"logging failed in {name}: {exc}", file=sys.stderr)

    def debug(self, message: str) -> None:
        self.log(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        self.log(LogLevel.INFO, message)

    def warning(self, message: str) -> None:
        self.log(LogLevel.WARNING, message)

    def error(self, message: str) -> None:
        self.log(LogLevel.ERROR, message)

    def critical(self, message: str) -> None:
        self.log(LogLevel.CRITICAL, message)

    # ---- testing hook --------------------------------------------------

    @classmethod
    def _reset_for_testing(cls) -> None:
        with cls._instance_lock:
            if cls._instance is not None:
                cls._instance.shutdown()
            cls._instance = None
