"""Write the formatted task to a local output file."""

from pathlib import Path


def save_task(text: str) -> Path:
    """Replace the example's output file with one formatted task."""
    directory = Path("output")
    directory.mkdir(exist_ok=True)
    target = directory / "task.txt"
    target.write_text(text + "\n", encoding="utf-8")
    return target
