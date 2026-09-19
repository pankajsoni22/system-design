from typing import Protocol

from logger import Logger, MemoryHandler


class SupportsInfo(Protocol):
    def info(self, message: str) -> None: ...


class HiddenOrderService:
    def place(self, order_id: int) -> None:
        Logger.get_instance().info(f"placed {order_id}")  # hidden: not in the signature


class OrderService:
    def __init__(self, logger: SupportsInfo) -> None:
        self.logger = logger  # explicit: visible, and replaceable in tests

    def place(self, order_id: int) -> None:
        self.logger.info(f"placed {order_id}")


class FakeLogger:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def info(self, message: str) -> None:
        self.messages.append(message)


def test_injected_logger_can_be_faked() -> None:
    fake = FakeLogger()
    OrderService(fake).place(7)
    assert fake.messages == ["placed 7"]


def test_hidden_dependency_needs_the_real_singleton() -> None:
    memory = MemoryHandler()
    Logger.get_instance().add_handler(memory)
    HiddenOrderService().place(7)
    assert memory.lines[0].endswith("placed 7")
