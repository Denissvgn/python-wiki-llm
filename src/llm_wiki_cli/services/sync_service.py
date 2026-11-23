"""Typed sync inputs and results shared by the CLI, the Python API and engines.

Importing this module is cheap; the sync implementation lives in
:mod:`llm_wiki_cli.services.sync_runtime` and is loaded on first use.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from llm_wiki_engine.path_policy import DEFAULT_WIKI_DIR

#: Page counters reported for a sync that reached the write stage.
SYNC_PAGE_COUNTERS = ("created", "updated", "metadata_only", "skipped", "deprecated", "preserved_semantic")

SyncStatus = Literal["synced", "up-to-date", "no-change"]


@dataclass(frozen=True)
class SyncRequest:
    """One incremental sync of ``wiki_root`` from ``source_root``.

    Field names describe the behaviour, not CLI flags: ``plugins=False`` is
    ``--no-plugins`` and ``cache=False`` is ``--no-cache``.
    """

    source_root: str | Path = "."
    wiki_root: str | Path = DEFAULT_WIKI_DIR
    dry_run: bool = False
    force: bool = False
    plugins: bool = True
    preserve_semantic: bool = True
    initialize_surfaces: Iterable[str] | None = None
    flow_categories: Iterable[str] | None = None
    exclude_tests: bool = False
    include_tests: Iterable[str] | None = None
    openapi_file: str | Path | None = None
    clear_openapi_file: bool = False
    source_selection: str | Path | None = None
    repair_evidence: Iterable[str] | None = None
    allow_external_source: bool = False
    rebuild_knowledge: bool = False
    knowledge_format: str | None = None
    helper_cache_dir: str | Path | None = None
    jobs: int = 1
    requested_jobs: int | Literal["auto"] | None = None
    cache: bool = True
    rebuild_cache: bool = False
    cache_dir: str | Path | None = None
    cache_stats: bool = False
    prune_storage: bool = False
    storage_recovery_dir: str | Path | None = None
    retire_missing_sources: Iterable[str] | None = None
    retire_missing_pages: Iterable[str] | None = None
    release_historical_pages: Iterable[str] | None = None
    expected_historical_release: str | None = None


@dataclass(frozen=True)
class SyncOutcome:
    """What one sync did; human-readable progress went to the host streams."""

    status: SyncStatus
    dry_run: bool
    pages: Mapping[str, int] = field(default_factory=dict)
    regenerated_evidence_pages: tuple[str, ...] = ()
    storage_cleanup: Mapping[str, Any] | None = None

    historical_release: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            **({"historical_release": dict(self.historical_release)} if self.historical_release is not None else {}),
            "status": self.status,
            "dry_run": self.dry_run,
            "pages": dict(self.pages),
            "regenerated_evidence_pages": list(self.regenerated_evidence_pages),
            "storage_cleanup": None if self.storage_cleanup is None else dict(self.storage_cleanup),
        }


class SyncError(Exception):
    """Sync stopped; ``exit_code`` is the status the CLI would exit with."""

    def __init__(self, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class SyncRequestError(SyncError):
    """The request's options are invalid or contradict each other."""


__all__ = [
    "SYNC_PAGE_COUNTERS",
    "SyncError",
    "SyncOutcome",
    "SyncRequest",
    "SyncRequestError",
    "SyncStatus",
]
