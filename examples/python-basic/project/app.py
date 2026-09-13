"""Build, format, and save one task."""

from models import Task
from service import format_task
from storage import save_task


def main() -> None:
    """Coordinate the model, formatting, and storage modules."""
    task = Task("Read the guide")
    text = format_task(task)
    save_task(text)


if __name__ == "__main__":
    main()
