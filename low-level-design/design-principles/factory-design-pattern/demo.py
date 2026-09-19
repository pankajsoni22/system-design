from notifications import NotificationService, NotifierFactory


def main() -> None:
    service = NotificationService(NotifierFactory.with_defaults())

    # The service only knows channel names. Which classes get built is the factory's job.
    print(service.send("email", "asha@example.com", "Your order has shipped"))

    # A user's saved preferences drive several channels at once.
    preferences = {
        "email": "asha@example.com",
        "sms": "+919876543210",
        "push": "device-token-1234",
        "fax": "555-0100",  # a channel we no longer support
    }
    for result in service.broadcast(preferences, "Your order has shipped"):
        status = "ok    " if result.delivered else "FAILED"
        print(f"{status} {result.channel:<5} {result.detail}")

    # Bad input is reported per channel, not raised.
    print(service.send("sms", "12345", "hello"))


if __name__ == "__main__":
    main()
