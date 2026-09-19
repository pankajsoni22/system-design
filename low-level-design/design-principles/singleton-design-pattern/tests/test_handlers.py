import io
import threading
import time
from pathlib import Path

from logger import ConsoleHandler, FileHandler, Logger, LogHandler


def test_file_handler_appends_lines(tmp_path: Path) -> None:
    path = tmp_path / "app.log"
    log = Logger.get_instance()
    log.add_handler(FileHandler(path))

    log.info("one")
    log.info("two")
    log.shutdown()

    lines = path.read_text(encoding="utf-8").splitlines()
    assert [line.rsplit(" ", 1)[-1] for line in lines] == ["one", "two"]


def test_console_handler_writes_to_the_given_stream() -> None:
    stream = io.StringIO()
    log = Logger.get_instance()
    log.add_handler(ConsoleHandler(stream))

    log.info("to the stream")

    assert stream.getvalue().endswith("to the stream\n")


def test_concurrent_file_writes_stay_intact_lines(tmp_path: Path) -> None:
    path = tmp_path / "app.log"
    log = Logger.get_instance()
    log.add_handler(FileHandler(path))
    thread_count, lines_each = 8, 200
    long_tail = "x" * 200  # long lines make interleaving easier to detect

    def worker(n: int) -> None:
        for i in range(lines_each):
            log.info(f"t{n}-{i}-{long_tail}")

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(thread_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    log.shutdown()

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == thread_count * lines_each
    assert all(line.endswith(long_tail) for line in lines)
    assert all(line.count(" [") == 2 for line in lines)  # level + thread, once each


class TwoStepHandler(LogHandler):
    """Emits in two steps, like a handler that writes a line and then a newline."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def _emit(self, line: str) -> None:
        self.parts.append(line)
        time.sleep(0.001)  # any pause lets another thread in, if nothing stops it
        self.parts.append("|")


def test_base_class_lock_keeps_multi_step_emits_together() -> None:
    handler = TwoStepHandler()
    log = Logger.get_instance()
    log.add_handler(handler)

    def worker() -> None:
        for _ in range(20):
            log.info("message")

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(handler.parts) == 8 * 20 * 2
    assert all(part == "|" for part in handler.parts[1::2])  # never a line in between
