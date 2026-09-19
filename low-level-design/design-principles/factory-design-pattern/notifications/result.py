from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    """What happened to one notification. Failures are reported, not raised."""

    delivered: bool
    channel: str
    detail: str
    attempts: int
