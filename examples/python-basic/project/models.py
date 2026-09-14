"""The task described by this small application."""

from dataclasses import dataclass


@dataclass
class Task:
    """A title and completion state for one task."""

    title: str
    done: bool = False
