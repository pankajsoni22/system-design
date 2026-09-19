from collections.abc import Iterator

import pytest

from logger import Logger


@pytest.fixture(autouse=True)
def fresh_logger() -> Iterator[None]:
    """Every test starts and ends with no Logger, so tests cannot leak state."""
    Logger._reset_for_testing()
    yield
    Logger._reset_for_testing()
