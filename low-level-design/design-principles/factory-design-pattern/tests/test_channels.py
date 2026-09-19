import pytest

from notifications import (
    Channel,
    EmailChannel,
    InvalidNotification,
    PushChannel,
    RecordingGateway,
    SmsChannel,
)


def make(channel_type: type[Channel]) -> tuple[Channel, RecordingGateway]:
    gateway = RecordingGateway()
    return channel_type(gateway), gateway


@pytest.mark.parametrize(
    ("channel_type", "recipient"),
    [
        (EmailChannel, "asha@example.com"),
        (SmsChannel, "+919876543210"),
        (PushChannel, "device-token-1234"),
    ],
)
def test_valid_recipient_and_message_pass(
    channel_type: type[Channel], recipient: str
) -> None:
    channel, _ = make(channel_type)
    channel.validate(recipient, "hello")  # does not raise


@pytest.mark.parametrize(
    ("channel_type", "recipient"),
    [
        (EmailChannel, "not-an-email"),
        (EmailChannel, "a@b"),
        (EmailChannel, "two words@example.com"),
        (SmsChannel, "9876543210"),  # missing the leading +
        (SmsChannel, "+0123456789"),  # country code cannot start with 0
        (SmsChannel, "+12"),  # too short
        (PushChannel, "short"),
        (PushChannel, "has spaces in it"),
    ],
)
def test_invalid_recipient_is_rejected(
    channel_type: type[Channel], recipient: str
) -> None:
    channel, _ = make(channel_type)
    with pytest.raises(InvalidNotification):
        channel.validate(recipient, "hello")


@pytest.mark.parametrize(
    ("channel_type", "recipient"),
    [
        (EmailChannel, "asha@example.com"),
        (SmsChannel, "+919876543210"),
        (PushChannel, "device-token-1234"),
    ],
)
def test_empty_message_is_rejected(channel_type: type[Channel], recipient: str) -> None:
    channel, _ = make(channel_type)
    with pytest.raises(InvalidNotification, match="empty"):
        channel.validate(recipient, "   ")


def test_sms_length_limit_is_exactly_160() -> None:
    channel, _ = make(SmsChannel)
    channel.validate("+919876543210", "x" * 160)
    with pytest.raises(InvalidNotification, match="161 characters"):
        channel.validate("+919876543210", "x" * 161)


def test_push_length_limit_is_exactly_200() -> None:
    channel, _ = make(PushChannel)
    channel.validate("device-token-1234", "x" * 200)
    with pytest.raises(InvalidNotification, match="201 characters"):
        channel.validate("device-token-1234", "x" * 201)


@pytest.mark.parametrize(
    ("channel_type", "recipient", "expected"),
    [
        (EmailChannel, "asha@example.com", "[email] Subject: Notification | hi"),
        (SmsChannel, "+919876543210", "[sms] hi"),
        (PushChannel, "device-token-1234", "[push] hi"),
    ],
)
def test_each_channel_formats_its_own_text(
    channel_type: type[Channel], recipient: str, expected: str
) -> None:
    channel, gateway = make(channel_type)

    channel.deliver(recipient, "hi")

    assert gateway.sent == [(recipient, expected)]
