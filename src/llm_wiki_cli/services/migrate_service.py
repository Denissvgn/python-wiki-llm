"""Typed migrate inputs and results shared by the CLI, the Python API and engines.

Importing this module is cheap; the migration lives in
:mod:`llm_wiki_cli.services.migrate_runtime` and is loaded on first use.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from llm_wiki_engine.path_policy import DEFAULT_WIKI_DIR

MigrateStatus = Literal["migrated", "planned", "chunk-applied", "up-to-date"]


@dataclass(frozen=True)
class MigrateRequest:
    """One migration of a wiki written by an older llm-wiki to current naming.

    ``chunk_size`` splits the work into reviewable chunks; ``chunk`` applies
    one of them (default: the first pending chunk) and ``plan_chunks`` only
    reports the chunk plan. ``plugins=False`` scans the source without
    project plugins.
    """

    source_root: str | Path = "."
    wiki_root: str | Path = DEFAULT_WIKI_DIR
    dry_run: bool = False
    chunk_size: int | None = None
    chunk: int | None = None
    plan_chunks: bool = False
    plugins: bool = True
    allow_external_source: bool = False
    source_selection: str | Path | None = None


@dataclass(frozen=True)
class MigrateOutcome:
    """What one migration did; human-readable progress went to the host streams.

    ``complete`` is true once the migration's final step has run (or, for a
    dry run, would run); a chunked migration reports which chunk it applied.
    """

    status: MigrateStatus
    dry_run: bool
    canonical_pages: int = 0
    archived_pages: int = 0
    unmatched_pages: int = 0
    chunk: int | None = None
    chunk_total: int | None = None
    page_operations: int = 0
    complete: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "dry_run": self.dry_run,
            "canonical_pages": self.canonical_pages,
            "archived_pages": self.archived_pages,
            "unmatched_pages": self.unmatched_pages,
            "chunk": self.chunk,
            "chunk_total": self.chunk_total,
            "page_operations": self.page_operations,
            "complete": self.complete,
        }


class MigrateError(Exception):
    """Migration stopped; ``exit_code`` is the status the CLI would exit with."""

    def __init__(self, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class MigrateRequestError(MigrateError):
    """The request's options are invalid or contradict each other."""


__all__ = [
    "MigrateError",
    "MigrateOutcome",
    "MigrateRequest",
    "MigrateRequestError",
    "MigrateStatus",
]
