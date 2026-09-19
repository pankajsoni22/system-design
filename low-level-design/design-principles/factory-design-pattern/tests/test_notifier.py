from typing import ClassVar

from notifications import (
    CallableNotifier,
    Channel,
    EmailChannel,
    EmailNotifier,
    Notifier,
    PushNotifier,
    RecordingGateway,
    SmsChannel,
    SmsNotifier,
    TransientChannelError,
)

EMAIL = "asha@example.com"


class FlakyGateway(RecordingGateway):
    """Fails the first `failures` sends with a retryable error, then works."""

    def __init__(self, failures: int) -> None:
        super().__init__()
        self.failures_left = failures
        self.calls = 0

    def send(self, address: str, text: str) -> None:
        self.calls += 1
        if self.failures_left > 0:
            self.failures_left -= 1
            raise TransientChannelError("provider timeout")
        super().send(address, text)


def test_success_on_first_attempt() -> None:
    gateway = RecordingGateway()
    result = EmailNotifier(gateway).notify(EMAIL, "hello")

    assert result.delivered
    assert (result.channel, result.attempts, result.detail) == ("email", 1, "delivered")
    assert len(gateway.sent) == 1


def test_transient_failures_are_retried_until_success() -> None:
    gateway = FlakyGateway(failures=2)
    result = EmailNotifier(gateway).notify(EMAIL, "hello")

    assert result.delivered
    assert result.attempts == 3
    assert gateway.calls == 3


def test_gives_up_after_max_attempts() -> None:
    gateway = FlakyGateway(failures=99)
    result = EmailNotifier(gateway).notify(EMAIL, "hello")

    assert not result.delivered
    assert result.attempts == EmailNotifier.max_attempts == 3
    assert gateway.calls == 3
    assert "gave up after 3 attempts: provider timeout" in result.detail


def test_each_notifier_carries_its_own_retry_budget() -> None:
    assert (EmailNotifier.max_attempts, SmsNotifier.max_attempts) == (3, 5)
    assert PushNotifier.max_attempts == 2

    gateway = FlakyGateway(failures=99)
    result = SmsNotifier(gateway).notify("+919876543210", "hello")
    assert (result.attempts, gateway.calls) == (5, 5)


def test_invalid_input_is_reported_and_never_sent() -> None:
    gateway = FlakyGateway(failures=0)
    result = EmailNotifier(gateway).notify("not-an-email", "hello")

    assert not result.delivered
    assert result.attempts == 0
    assert "not an email address" in result.detail
    assert gateway.calls == 0


def test_factory_method_is_a_test_seam() -> None:
    """Overriding create_channel swaps the product without touching the workflow."""

    class ScriptedChannel(Channel):
        name: ClassVar[str] = "scripted"

        def __init__(self) -> None:
            super().__init__(RecordingGateway())
            self.delivered: list[str] = []

        def validate(self, recipient: str, message: str) -> None:
            return

        def deliver(self, recipient: str, message: str) -> None:
            self.delivered.append(message)

    class TestNotifier(Notifier):
        def __init__(self) -> None:
            super().__init__()
            self.channel = ScriptedChannel()

        def create_channel(self) -> Channel:
            return self.channel

    notifier = TestNotifier()
    result = notifier.notify("anyone", "hello")

    assert result.delivered
    assert result.channel == "scripted"
    assert notifier.channel.delivered == ["hello"]


def test_create_channel_is_called_for_every_notification() -> None:
    class CountingNotifier(EmailNotifier):
        created = 0

        def create_channel(self) -> Channel:
            self.created += 1
            return super().create_channel()

    notifier = CountingNotifier(RecordingGateway())
    notifier.notify(EMAIL, "one")
    notifier.notify(EMAIL, "two")

    assert notifier.created == 2


def test_callable_notifier_behaves_like_a_subclass() -> None:
    gateway = RecordingGateway()
    result = CallableNotifier(EmailChannel, gateway).notify(EMAIL, "hello")

    assert result.delivered
    assert gateway.sent[0][1].startswith("[email]")


def test_callable_notifier_takes_its_retry_budget_as_an_argument() -> None:
    gateway = FlakyGateway(failures=99)
    result = CallableNotifier(SmsChannel, gateway, max_attempts=4).notify(
        "+919876543210", "hello"
    )

    assert (result.delivered, result.attempts, gateway.calls) == (False, 4, 4)
