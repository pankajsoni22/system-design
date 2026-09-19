import pytest

from notifications import (
    NotificationService,
    NotifierFactory,
    RecordingGateway,
    UnknownChannelError,
)


def make_service() -> tuple[NotificationService, RecordingGateway]:
    gateway = RecordingGateway()
    return NotificationService(NotifierFactory.with_defaults(gateway)), gateway


def test_send_routes_by_channel_name() -> None:
    service, gateway = make_service()

    result = service.send("sms", "+919876543210", "hello")

    assert result.delivered
    assert result.channel == "sms"
    assert gateway.sent == [("+919876543210", "[sms] hello")]


def test_send_raises_for_an_unknown_channel() -> None:
    service, gateway = make_service()

    with pytest.raises(UnknownChannelError):
        service.send("fax", "555-0100", "hello")

    assert gateway.sent == []


def test_broadcast_uses_every_channel_the_user_has() -> None:
    service, gateway = make_service()

    results = service.broadcast(
        {"email": "asha@example.com", "sms": "+919876543210"}, "hello"
    )

    assert [r.channel for r in results] == ["email", "sms"]
    assert all(r.delivered for r in results)
    assert len(gateway.sent) == 2


def test_broadcast_turns_an_unknown_channel_into_a_failed_result() -> None:
    service, gateway = make_service()

    results = service.broadcast(
        {"fax": "555-0100", "email": "asha@example.com", "push": "device-token-1234"},
        "hello",
    )

    assert [r.delivered for r in results] == [False, True, True]
    assert "unknown channel 'fax'" in results[0].detail
    assert len(gateway.sent) == 2  # the working channels were not held up


def test_broadcast_reports_bad_addresses_per_channel() -> None:
    service, _ = make_service()

    results = service.broadcast({"email": "asha@example.com", "sms": "12345"}, "hello")

    assert [r.delivered for r in results] == [True, False]
    assert "E.164" in results[1].detail
