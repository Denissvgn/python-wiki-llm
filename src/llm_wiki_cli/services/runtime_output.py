"""Best-effort implicit output and preflighted operator-selected destinations."""

from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


class RuntimeOutputError(ValueError):
    """An explicitly requested runtime destination is unusable."""


WarningSink = Callable[[str], None]


def stderr_warning(message: str) -> None:
    """Warnings do not interfere with machine-readable stdout or computation."""
    try:
        print(f"Warning: {message}", file=sys.stderr, flush=True)
    except (OSError, ValueError):
        pass


def warn(sink: WarningSink | None, message: str) -> None:
    if sink is not None:
        try:
            sink(message)
        except Exception:
            pass


@dataclass
class RuntimeDestination:
    path: Path | None
    explicit: bool = False
    status: str = "disabled"
    error: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "path": None if self.path is None else str(self.path),
            "explicit": self.explicit,
            "status": self.status,
            "error": self.error,
        }


def preflight_output_path(path: Path) -> None:
    """Probe same-directory creation/replacement without touching the real output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not path.is_file():
        raise OSError(f"Output is not a regular file: {path}")
    temporary: list[str] = []
    try:
        for _ in range(2):
            fd, name = tempfile.mkstemp(prefix=".llm-wiki-probe-", dir=path.parent)
            temporary.append(name)
            with os.fdopen(fd, "wb") as stream:
                stream.write(b"llm-wiki output preflight\n")
        os.replace(temporary[0], temporary[1])
    finally:
        for name in temporary:
            try:
                os.unlink(name)
            except FileNotFoundError:
                pass


def prepare_destination(
    path: Path | None,
    *,
    kind: str,
    explicit: bool = False,
    warning: WarningSink | None = None,
) -> RuntimeDestination:
    if path is None:
        return RuntimeDestination(None)
    destination = RuntimeDestination(path, explicit, "pending")
    try:
        preflight_output_path(path)
    except (OSError, ValueError, RuntimeError) as exc:
        destination.status = "failed"
        destination.error = str(exc)
        if explicit:
            raise RuntimeOutputError(
                f"Cannot write explicit {kind} destination {path}: {exc}"
            ) from exc
        remedy = (
            " Use --cache-dir with a writable directory."
            if kind == "cache"
            else " Use --report or --no-report."
        )
        warn(warning, f"Implicit {kind} output unavailable at {path}: {exc}.{remedy}")
    return destination
