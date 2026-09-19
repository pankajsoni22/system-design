import tempfile
import threading
from pathlib import Path

from logger import ConsoleHandler, FileHandler, Logger, LogLevel


def worker(name: str) -> None:
    log = Logger.get_instance()  # same object in every thread, nothing passed in
    for i in range(2):
        log.info(f"{name} processed item {i}")


def main() -> None:
    log_file = Path(tempfile.mkdtemp()) / "app.log"

    log = Logger.get_instance()
    log.set_level(LogLevel.DEBUG)
    log.add_handler(ConsoleHandler())
    log.add_handler(FileHandler(log_file))

    log.debug("application starting")
    threads = [
        threading.Thread(target=worker, args=(f"worker-{n}",), name=f"worker-{n}")
        for n in range(3)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("same instance everywhere:", Logger.get_instance() is log)
    try:
        Logger()
    except TypeError as error:
        print("direct construction is blocked:", error)

    log.shutdown()
    print("lines in the log file:", len(log_file.read_text().splitlines()))


if __name__ == "__main__":
    main()
