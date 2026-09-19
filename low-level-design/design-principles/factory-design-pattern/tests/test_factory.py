from typing import ClassVar

import pytest

from notifications import (
    CallableNotifier,
    Channel,
    EmailNotifier,
    Notifier,
    NotifierFactory,
    PushNotifier,
    RecordingGateway,
    SmsNotifier,
    UnknownChannelError,
)


def test_defaults_build_the_matching_notifier() -> None:
    factory = NotifierFactory.with_defaults()

    assert type(factory.create("email")) is EmailNotifier
    assert type(factory.create("sms")) is SmsNotifier
    assert type(factory.create("push")) is PushNotifier
    assert factory.names == ("email", "push", "sms")


def test_every_call_builds_a_fresh_notifier() -> None:
    factory = NotifierFactory.with_defaults()
    assert factory.create("email") is not factory.create("email")


def test_unknown_channel_error_lists_what_is_available() -> None:
    factory = NotifierFactory.with_defaults()

    with pytest.raises(UnknownChannelError) as error:
        factory.create("fax")

    message = str(error.value)
    assert "'fax'" in message
    assert "email, push, sms" in message


def test_unknown_channel_on_an_empty_factory() -> None:
    with pytest.raises(UnknownChannelError, match="available: none"):
        NotifierFactory().create("email")


def test_registering_a_name_twice_is_an_error() -> None:
    factory = NotifierFactory.with_defaults()
    with pytest.raises(ValueError, match="already registered"):
        factory.register("email", EmailNotifier)


def test_gateway_is_passed_down_to_the_channels() -> None:
    gateway = RecordingGateway()
    factory = NotifierFactory.with_defaults(gateway)

    factory.create("email").notify("asha@example.com", "hello")

    assert len(gateway.sent) == 1


def test_new_channel_needs_no_change_to_existing_code() -> None:
    """The open/closed check: a channel invented here works through the factory."""

    class SlackChannel(Channel):
        name: ClassVar[str] = "slack"

        def validate(self, recipient: str, message: str) -> None:
            return

        def deliver(self, recipient: str, message: str) -> None:
            self._gateway.send(recipient, f"[slack] {message}")

    class SlackNotifier(Notifier):
        def create_channel(self) -> Channel:
            return SlackChannel(self._gateway)

    gateway = RecordingGateway()
    factory = NotifierFactory.with_defaults(gateway)
    factory.register("slack", lambda: SlackNotifier(gateway))

    result = factory.create("slack").notify("#alerts", "deploy finished")

    assert result.delivered
    assert gateway.sent == [("#alerts", "[slack] deploy finished")]
    assert "slack" in factory.names


def test_new_channel_can_also_skip_the_notifier_subclass() -> None:
    """The Pythonic route: one new class (the channel), no creator subclass."""

    class TelegramChannel(Channel):
        name: ClassVar[str] = "telegram"

        def validate(self, recipient: str, message: str) -> None:
            return

        def deliver(self, recipient: str, message: str) -> None:
            self._gateway.send(recipient, f"[telegram] {message}")

    gateway = RecordingGateway()
    factory = NotifierFactory()
    factory.register("telegram", lambda: CallableNotifier(TelegramChannel, gateway))

    result = factory.create("telegram").notify("@asha", "hi")

    assert result.delivered
    assert gateway.sent == [("@asha", "[telegram] hi")]
