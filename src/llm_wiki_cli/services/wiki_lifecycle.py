"""Read-only classification for wiki bootstrap, sync, and migration routing."""

from __future__ import annotations

import json
import shlex
from enum import Enum
from pathlib import Path
from typing import Union

from ..config import AGENT_CHOICES
from .sync_manifest import MANIFEST_FILENAME
from .wiki_scaffold import (
    INITIAL_WIKI_INDEX_MARKDOWN,
    INITIAL_WIKI_LOG_MARKDOWN,
)
from .wiki_surface import iter_page_kinds


class WikiLifecycleState(str, Enum):
    """One unambiguous lifecycle route for a wiki target."""

    FIRST_USE = "first-use"
    SYNC_SEEDABLE = "sync-seedable"
    MIGRATION_REQUIRED = "migration-required"
    MANAGED = "managed"


def is_pristine_wiki_target(wiki_dir: Union[str, Path]) -> bool:
    """Return whether a target is absent, empty, or the exact init scaffold."""

    root = Path(wiki_dir)
    if root.is_symlink():
        return False
    if not root.exists():
        return True
    if not root.is_dir():
        return False

    scaffold_directories = {
        entry.directory
        for entry in iter_page_kinds()
        if entry.directory is not None
    }
    allowed_gitkeeps = {".gitkeep"} | {
        f"{directory}/.gitkeep" for directory in scaffold_directories
    }
    expected_paths = {
        *scaffold_directories,
        *allowed_gitkeeps,
        "index.md",
        "log.md",
    }
    try:
        entries = sorted(root.rglob("*"))
    except OSError:
        return False
    if not entries:
        return True

    paths_by_relative: dict[str, Path] = {}
    for path in entries:
        if path.is_symlink():
            return False
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            return False
        paths_by_relative[relative] = path

    actual_paths = set(paths_by_relative)
    if actual_paths not in (
        expected_paths,
        expected_paths | {".llm-wiki-agent"},
    ):
        return False

    for relative, path in paths_by_relative.items():
        if relative in scaffold_directories:
            if not path.is_dir():
                return False
            continue
        if not path.is_file():
            return False
        try:
            if relative in allowed_gitkeeps:
                if path.stat().st_size != 0:
                    return False
            elif relative == "index.md":
                if path.read_text(encoding="utf-8") != INITIAL_WIKI_INDEX_MARKDOWN:
                    return False
            elif relative == "log.md":
                if path.read_text(encoding="utf-8") != INITIAL_WIKI_LOG_MARKDOWN:
                    return False
            elif relative == ".llm-wiki-agent":
                raw_config = path.read_text(encoding="utf-8")
                config = json.loads(raw_config)
                if (
                    not isinstance(config, dict)
                    or set(config)
                    != {
                        "agent",
                        "quality_hints",
                        "reference_skill",
                        "issue_reporting",
                    }
                    or config["agent"] not in AGENT_CHOICES
                    or any(
                        type(config[key]) is not bool
                        for key in (
                            "quality_hints",
                            "reference_skill",
                            "issue_reporting",
                        )
                    )
                ):
                    return False
                canonical_config = {
                    "agent": config["agent"],
                    "quality_hints": config["quality_hints"],
                    "reference_skill": config["reference_skill"],
                    "issue_reporting": config["issue_reporting"],
                }
                if raw_config != json.dumps(canonical_config, indent=2) + "\n":
                    return False
        except (KeyError, OSError, TypeError, UnicodeError, ValueError):
            return False
    return True


def classify_wiki_lifecycle(
    wiki_dir: Union[str, Path],
) -> WikiLifecycleState:
    """Classify a target without reading source code or mutating the wiki."""

    root = Path(wiki_dir)
    manifest = root / MANIFEST_FILENAME
    if manifest.exists() or manifest.is_symlink():
        return WikiLifecycleState.MANAGED
    if is_pristine_wiki_target(root):
        return WikiLifecycleState.FIRST_USE
    index = root / "index.md"
    if root.is_dir() and index.is_file() and not index.is_symlink():
        return WikiLifecycleState.SYNC_SEEDABLE
    return WikiLifecycleState.MIGRATION_REQUIRED


def bootstrap_guidance(*, src_dir: str, wiki_dir: Union[str, Path]) -> str:
    """Return a path-safe first-use bootstrap command."""

    return (
        "Run "
        f"`llm-wiki bootstrap --src-dir {shlex.quote(src_dir)} "
        f"--wiki-dir {shlex.quote(str(wiki_dir))}` "
        "to create the initial wiki and manifest."
    )


def migration_guidance(*, src_dir: str, wiki_dir: Union[str, Path]) -> str:
    """Return a path-safe migration preview command."""

    return (
        "Preview the existing wiki migration with "
        f"`llm-wiki migrate --dry-run --src-dir {shlex.quote(src_dir)} "
        f"--wiki-dir {shlex.quote(str(wiki_dir))}`."
    )


def sync_guidance(*, src_dir: str, wiki_dir: Union[str, Path]) -> str:
    """Return a path-safe manifest-seeding sync command."""

    return (
        "Seed the existing wiki safely with "
        f"`llm-wiki sync --jobs 1 --src-dir {shlex.quote(src_dir)} "
        f"--wiki-dir {shlex.quote(str(wiki_dir))}`."
    )


__all__ = [
    "WikiLifecycleState",
    "bootstrap_guidance",
    "classify_wiki_lifecycle",
    "is_pristine_wiki_target",
    "migration_guidance",
    "sync_guidance",
]
