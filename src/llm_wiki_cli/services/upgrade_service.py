"""Typed upgrade inputs and results shared by the CLI, the Python API and engines.

Importing this module is cheap; the upgrade lives in
:mod:`llm_wiki_cli.services.upgrade_runtime` and is loaded on first use.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .path_policy import DEFAULT_WIKI_DIR

UpgradeStatus = Literal["complete", "source-cleanup-pending"]


@dataclass(frozen=True)
class UpgradeRequest:
    """One in-place refresh of the managed agent schema, skills and wiki layout.

    ``None`` keeps the stored preference: ``agent`` and the
    ``quality_hints``/``reference_skill``/``issue_reporting`` switches fall
    back to the local agent config, and ``source_root`` to the recorded
    source root. ``cleanup_source_agent`` names the previous agent whose
    managed files may be removed after a switch.
    """

    wiki_root: str | Path = DEFAULT_WIKI_DIR
    source_root: str | Path | None = None
    agent: str | None = None
    cleanup_source_agent: str | None = None
    quality_hints: bool | None = None
    reference_skill: bool | None = None
    issue_reporting: bool | None = None
    source_selection: str | Path | None = None
    helper_cache_dir: str | Path | None = None


@dataclass(frozen=True)
class UpgradeOutcome:
    """What one upgrade did; human-readable progress went to the host streams.

    ``status`` is ``source-cleanup-pending`` when the target is usable but the
    previous agent's files were kept for an explicit retry.
    """

    status: UpgradeStatus
    agent: str
    previous_agent: str | None = None
    schema_file: str = ""
    reference_skill: str = ""
    legacy_hooks_removed: int = 0
    created_entries: Sequence[str] = ()
    recovery_dir: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "agent": self.agent,
            "previous_agent": self.previous_agent,
            "schema_file": self.schema_file,
            "reference_skill": self.reference_skill,
            "legacy_hooks_removed": self.legacy_hooks_removed,
            "created_entries": list(self.created_entries),
            "recovery_dir": self.recovery_dir,
        }


class UpgradeError(Exception):
    """Upgrade stopped; ``exit_code`` is the status the CLI would exit with."""

    def __init__(self, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class UpgradeRequestError(UpgradeError):
    """The request names a path the workspace policy rejects."""


__all__ = [
    "UpgradeError",
    "UpgradeOutcome",
    "UpgradeRequest",
    "UpgradeRequestError",
    "UpgradeStatus",
]
