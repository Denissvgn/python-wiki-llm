"""A naming convention recognized by the documentation-hooks sample plugin."""

from storage import save_result


def handle_task(title: str) -> str:
    """Record the normalized title and return it to the caller."""
    result = title.strip()
    save_result(result)
    return result
