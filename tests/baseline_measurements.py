"""Deterministic measurements for text and JSON golden baselines."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping


def measure_text(content: str) -> dict[str, int | str]:
    """Return stable whitespace, code-point, line, and UTF-8 byte metrics."""

    if not isinstance(content, str):
        raise TypeError("content must be text")
    return {
        "words": len(content.split()),
        "characters": len(content),
        "lines": len(content.splitlines()),
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }


def assert_text_baseline(
    label: str,
    content: str,
    expected: Mapping[str, object],
) -> None:
    """Compare one text value with an observed baseline and report useful sizes."""

    actual = measure_text(content)
    selected_expected = {key: expected[key] for key in actual}
    if actual == selected_expected:
        return
    raise AssertionError(
        f"{label} changed: measured words={actual['words']}, "
        f"characters={actual['characters']}, lines={actual['lines']}, "
        f"sha256={actual['sha256']}; expected words={selected_expected['words']}, "
        f"characters={selected_expected['characters']}, "
        f"lines={selected_expected['lines']}, "
        f"sha256={selected_expected['sha256']}"
    )
