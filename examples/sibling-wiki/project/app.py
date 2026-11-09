"""Accounts carry the display name chosen by their owner."""


class Account:
    """One named account."""

    def __init__(self, name: str):
        self.name = name
