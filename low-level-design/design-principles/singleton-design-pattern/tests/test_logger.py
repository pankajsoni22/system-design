from datetime import UTC, datetime

import pytest

from logger import (
    Logger,
    LogHandler,
    LogLevel,
    LogRecord,
    MemoryHandler,
    SimpleFormatter,
)


class BrokenHandler(LogHandler):
    def _emit(self, line: str) -> None:
        raise OSError("disk full")


def test_default_level_is_info() -> None:
    memory = MemoryHandler()
    log = Logger.get_instance()
    log.add_handler(memory)

    log.debug("hidden")
    log.info("shown")

    assert len(memory.lines) == 1
    assert memory.lines[0].endswith("shown")


def test_set_level_filters_everything_below() -> None:
    memory = MemoryHandler()
    log = Logger.get_instance()
    log.add_handler(memory)
    log.set_level(LogLevel.ERROR)

    log.warning("no")
    log.error("yes")
    log.critical("also yes")

    assert [line.rsplit(" ", 1)[-1] for line in memory.lines] == ["yes", "yes"]


def test_every_handler_receives_the_record() -> None:
    first, second = MemoryHandler(), MemoryHandler()
    log = Logger.get_instance()
    log.add_handler(first)
    log.add_handler(second)

    log.info("fan out")

    assert len(first.lines) == len(second.lines) == 1


def test_a_failing_handler_does_not_stop_the_others(
    capsys: pytest.CaptureFixture[str],
) -> None:
    memory = MemoryHandler()
    log = Logger.get_instance()
    log.add_handler(BrokenHandler())
    log.add_handler(memory)

    log.info("still delivered")

    assert len(memory.lines) == 1
    assert "logging failed in BrokenHandler: disk full" in capsys.readouterr().err


def test_shutdown_removes_handlers() -> None:
    log = Logger.get_instance()
    log.add_handler(MemoryHandler())
    log.shutdown()
    assert log.handlers == ()


def test_simple_formatter_output() -> None:
    record = LogRecord(
        timestamp=datetime(2026, 9, 19, 10, 15, 30, 123000, tzinfo=UTC),
        level=LogLevel.INFO,
        message="hello",
        thread_name="MainThread",
    )
    assert SimpleFormatter().format(record) == (
        "2026-09-19T10:15:30.123+00:00 [INFO    ] [MainThread] hello"
    )


def test_a_custom_formatter_can_be_plugged_in() -> None:
    class ShoutingFormatter:
        def format(self, record: LogRecord) -> str:
            return record.message.upper()

    memory = MemoryHandler(formatter=ShoutingFormatter())
    log = Logger.get_instance()
    log.add_handler(memory)

    log.info("quiet")

    assert memory.lines == ["QUIET"]
