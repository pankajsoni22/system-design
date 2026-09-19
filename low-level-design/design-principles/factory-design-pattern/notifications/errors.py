class InvalidNotification(ValueError):
    """The recipient or message is not acceptable for this channel. Never retried."""


class TransientChannelError(Exception):
    """A delivery attempt failed in a way that may succeed if retried."""


class UnknownChannelError(LookupError):
    """No notifier is registered under the requested channel name."""
