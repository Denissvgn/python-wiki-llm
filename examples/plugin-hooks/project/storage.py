"""Keep the task result in a local file."""

from pathlib import Path


def save_result(result: str) -> None:
    """Write one result; documentation generation never executes this body."""
    directory = Path("output")
    directory.mkdir(exist_ok=True)
    (directory / "result.txt").write_text(result + "\n", encoding="utf-8")
