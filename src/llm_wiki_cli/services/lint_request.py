"""Typed lint inputs shared by the CLI, the Python API and engines.

Importing this module is cheap; the checks live in
:mod:`llm_wiki_cli.services.lint_service` and are loaded on first use.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from llm_wiki_engine.path_policy import DEFAULT_WIKI_DIR


@dataclass(frozen=True)
class LintRequest:
    """One lint of ``wiki_root`` against ``source_root``.

    Field names describe the behaviour, not CLI flags: ``cache=False`` is
    ``--no-cache`` and ``allow_external_source`` is ``--allow-external-src``.
    ``media_size_warn_bytes=None`` keeps the default media size threshold.
    ``plugins=False`` skips project plugins, as ``doctor`` does.
    """

    wiki_root: str | Path = DEFAULT_WIKI_DIR
    source_root: str | Path = "."
    strict: bool = False
    plugins: bool = True
    knowledge_drift_report: bool = False
    allow_external_source: bool = False
    source_selection: str | Path | None = None
    include_tests: Iterable[str] | None = None
    helper_cache_dir: str | Path | None = None
    media_size_warn_bytes: int | None = None
    jobs: int = 1
    requested_jobs: int | Literal["auto"] | None = None
    cache: bool = True
    rebuild_cache: bool = False
    cache_dir: str | Path | None = None
    cache_stats: bool = False
    require_fresh: bool = False


class LintRequestError(ValueError):
    """The lint request names a path the workspace policy rejects."""


__all__ = ["LintRequest", "LintRequestError"]
