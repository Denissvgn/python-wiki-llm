"""Report the disk space llm-wiki owns for one wiki and reclaim it on request."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from llm_wiki_engine.knowledge_storage import KnowledgeStorageError
from llm_wiki_engine.layout import DEFAULT_LAYOUT
from llm_wiki_engine.knowledge_storage_io import _absolute_path

from .inventory_cache import CACHE_FILENAME, ENV_CACHE_DIR
from .sync_analysis_cache import FILENAME as ANALYSIS_FILENAME

SCHEMA = "llm-wiki-storage-usage/v1"
DEFAULT_RECOVERY_AGE_DAYS = 7
MAX_SCANNED_FILES = 2_000_000

WIKI_STORE = "wiki-store"
MAINTENANCE_RECOVERY = "maintenance-recovery"
STORAGE_RECOVERY = "storage-recovery"
UPGRADE_RECOVERY = "upgrade-recovery"
CACHES = "caches"
HELPERS = "helpers"

# Classes a caller may reclaim. The wiki store is cleaned by ``prune-storage``
# against a validated snapshot, and maintenance recovery is retired by the
# writer that owns it, so neither is deleted from here.
RECLAIMABLE = (CACHES, HELPERS, STORAGE_RECOVERY, UPGRADE_RECOVERY)
_AGED = frozenset({STORAGE_RECOVERY, UPGRADE_RECOVERY})

_NOTES = {
    WIKI_STORE: "Committed knowledge and manifest objects. Remove unreferenced ones with knowledge prune-storage or sync --prune-storage.",
    MAINTENANCE_RECOVERY: "Recovery copies of adopted wiki writes. A writing sync retires old ones and those of removed worktrees.",
    STORAGE_RECOVERY: "Copies of objects removed by storage cleanup or migration.",
    UPGRADE_RECOVERY: "Recovery copies written by bootstrap and upgrade in the system temporary directory.",
    CACHES: "Extraction and analysis caches. The next run rebuilds them.",
    HELPERS: "Prepared language helpers. Rebuilding them needs prepare-extractors and its toolchains.",
}


def _measure(path: Path, budget: list[int]) -> tuple[int, int]:
    """Return (bytes, files) below ``path`` without following symbolic links."""
    try:
        if path.is_symlink() or not path.exists():
            return 0, 0
        if path.is_file():
            budget[0] -= 1
            return path.stat().st_size, 1
    except OSError:
        return 0, 0
    total = files = 0
    stack = [path]
    while stack:
        try:
            entries = list(os.scandir(stack.pop()))
        except OSError:
            continue
        for entry in entries:
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    stack.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    budget[0] -= 1
                    if budget[0] < 0:
                        raise KnowledgeStorageError(
                            "storage-usage", "scan exceeds its file bound", code="storage-limit"
                        )
                    total += entry.stat(follow_symlinks=False).st_size
                    files += 1
            except OSError:
                continue
    return total, files


def _git_directories(wiki: Path) -> list[Path]:
    """Return this checkout's Git directory and, for a worktree, the shared one."""
    found: list[Path] = []
    for flag in ("--absolute-git-dir", "--git-common-dir"):
        try:
            result = subprocess.run(  # noqa: S603 - fixed arguments, no shell
                ["git", "-C", str(wiki), "rev-parse", flag],  # noqa: S607
                capture_output=True, text=True, timeout=10, check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        text = result.stdout.strip()
        if result.returncode or not text:
            continue
        candidate = Path(text)
        if not candidate.is_absolute():
            candidate = wiki / candidate
        try:
            candidate = candidate.resolve()
        except OSError:
            continue
        if candidate.is_dir() and candidate not in found:
            found.append(candidate)
    return found


def _candidates(wiki: Path) -> list[tuple[str, Path]]:
    rows: list[tuple[str, Path]] = [
        (WIKI_STORE, wiki / DEFAULT_LAYOUT.knowledge_store),
        (WIKI_STORE, wiki / DEFAULT_LAYOUT.manifest_objects),
    ]
    bases = _git_directories(wiki)
    configured = os.environ.get(ENV_CACHE_DIR)
    cache_bases = list(bases)
    if configured:
        base = Path(configured).expanduser()
        base = base if base.is_absolute() else Path.cwd() / base
        try:
            base = base.resolve()
        except OSError:
            base = None  # type: ignore[assignment]
        if base is not None and base not in cache_bases:
            cache_bases.append(base)
    for base in bases:
        rows.append((MAINTENANCE_RECOVERY, base / "maintenance-preimages"))
        rows.append((STORAGE_RECOVERY, base / "llm-wiki-storage-recovery"))
    if not bases:
        rows.append((MAINTENANCE_RECOVERY, wiki.parent / ".llm-wiki-maintenance-recovery"))
        rows.append((STORAGE_RECOVERY, wiki.parent / ".llm-wiki-storage-recovery"))
    for base in cache_bases:
        rows.append((CACHES, base / CACHE_FILENAME))
        rows.append((CACHES, base / ANALYSIS_FILENAME))
        rows.append((CACHES, base / (ANALYSIS_FILENAME + ".objects")))
        rows.append((HELPERS, base / "llm-wiki-extractors"))
    identity = hashlib.sha256(str(wiki).encode()).hexdigest()[:20]
    upgrade = Path(tempfile.gettempdir()).resolve() / "llm-wiki-upgrade-recovery"
    try:
        entries = sorted(upgrade.iterdir()) if upgrade.is_dir() and not upgrade.is_symlink() else []
    except OSError:
        entries = []
    rows.extend(
        (UPGRADE_RECOVERY, entry) for entry in entries if entry.name.startswith(identity + "-")
    )
    return rows


def _aged_entries(kind: str, path: Path, deadline: float) -> list[Path]:
    """Return what an aged class may remove: whole runs last changed before the deadline."""
    if kind == UPGRADE_RECOVERY:
        targets = [path]
    else:
        try:
            targets = sorted(
                entry for group in path.iterdir() if group.is_dir() and not group.is_symlink()
                for entry in group.iterdir()
            ) + sorted(entry for entry in path.iterdir() if not entry.is_dir())
        except OSError:
            return []
    selected = []
    for target in targets:
        try:
            if not target.is_symlink() and target.stat().st_mtime <= deadline:
                selected.append(target)
        except OSError:
            continue
    return selected


def _remove(path: Path) -> None:
    if path.is_symlink():
        raise KnowledgeStorageError("reclaim", f"refusing to follow a symbolic link: {path}")
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def storage_usage(
    wiki_dir: str | Path,
    *,
    reclaim: list[str] | tuple[str, ...] = (),
    older_than_days: int = DEFAULT_RECOVERY_AGE_DAYS,
    apply: bool = False,
) -> dict[str, Any]:
    """List every location llm-wiki owns for ``wiki_dir`` and optionally reclaim some.

    The report is read-only. ``reclaim`` names classes to remove; nothing is
    deleted unless ``apply`` is true. Recovery classes only give up entries
    older than ``older_than_days``.
    """
    if type(apply) is not bool:
        raise KnowledgeStorageError("apply", "must be a boolean")
    if type(older_than_days) is not int or not 0 <= older_than_days <= 3650:
        raise KnowledgeStorageError("older_than_days", "must be between 0 and 3650")
    requested = list(dict.fromkeys(reclaim))
    unknown = [name for name in requested if name not in RECLAIMABLE]
    if unknown:
        raise KnowledgeStorageError(
            "reclaim", f"unknown or protected class: {', '.join(unknown)}; choose from {', '.join(RECLAIMABLE)}"
        )
    if apply and not requested:
        raise KnowledgeStorageError("apply", "requires at least one --reclaim class")
    wiki = _absolute_path(Path(wiki_dir))
    budget = [MAX_SCANNED_FILES]
    deadline = time.time() - older_than_days * 86_400
    locations: list[dict[str, Any]] = []
    totals: dict[str, dict[str, int]] = {}
    planned: list[tuple[str, Path, int]] = []
    for kind, path in _candidates(wiki):
        size, files = _measure(path, budget)
        if not files and not path.exists():
            continue
        locations.append({
            "class": kind, "path": str(path), "bytes": size, "files": files,
            "reclaimable": kind in RECLAIMABLE,
        })
        bucket = totals.setdefault(kind, {"bytes": 0, "files": 0})
        bucket["bytes"] += size
        bucket["files"] += files
        if kind in requested:
            targets = _aged_entries(kind, path, deadline) if kind in _AGED else [path]
            planned.extend((kind, target, _measure(target, budget)[0]) for target in targets)
    removed: list[dict[str, Any]] = []
    if apply:
        for kind, target, size in planned:
            _remove(target)
            removed.append({"class": kind, "path": str(target), "bytes": size})
    return {
        "schema_version": SCHEMA,
        "wiki_dir": str(wiki),
        "ok": True,
        "total_bytes": sum(row["bytes"] for row in totals.values()),
        "totals": {name: totals[name] for name in sorted(totals)},
        "locations": locations,
        "notes": {name: _NOTES[name] for name in sorted(totals)},
        "reclaim": {
            "requested": requested,
            "older_than_days": older_than_days,
            "applied": apply,
            "candidates": [
                {"class": kind, "path": str(target), "bytes": size} for kind, target, size in planned
            ],
            "candidate_bytes": sum(size for _kind, _target, size in planned),
            "removed": removed,
            "removed_bytes": sum(row["bytes"] for row in removed),
        },
    }
