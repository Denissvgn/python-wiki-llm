"""Turn a task into a line of plain text."""

from models import Task


def format_task(task: Task) -> str:
    """Keep the title intact and prefix it with its completion state."""
    marker = "x" if task.done else " "
    return f"[{marker}] {task.title}"
