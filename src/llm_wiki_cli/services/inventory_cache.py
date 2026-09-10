"""Persistent inventory cache used by lint and CI validation."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from .. import __version__ as LLM_WIKI_VERSION
from ..config import (
    AGENT_WORKTREE_DIR_PATTERNS,
    COMPOSE_PATTERNS,
    DOCKERFILE_PATTERNS,
    EXCLUDED_DIRS,
    is_agent_worktree_path,
)
from ..extractors.common import LANGUAGE_EXTENSIONS
from .plugins import lock_path, plugin_store
from .source_snapshot import SourceFile, SourceSnapshot
from .io import write_json_atomic
from .progress import observed_phase
from .runtime_output import (
    RuntimeDestination,
    RuntimeOutputError,
    WarningSink,
    prepare_destination,
    stderr_warning,
    warn,
)

CACHE_FILENAME = "llm-wiki-inventory-cache.json"
CACHE_SCHEMA = "inventory-v3"
CACHE_VERSION = 3
ENV_CACHE_DIR = "LLM_WIKI_CACHE_DIR"


@dataclass(frozen=True)
class InventoryCacheOptions:
    """Runtime cache controls for inventory-producing commands."""

    enabled: bool = False
    rebuild: bool = False
    cache_dir: str | None = None
    stats_enabled: bool = False
    destination: RuntimeDestination | None = field(
        default=None, repr=False, compare=False
    )
    warning: WarningSink | None = field(default=None, repr=False, compare=False)


@dataclass
class InventoryCacheStats:
    enabled: bool = False
    path: str | None = None
    status: str = "disabled"
    hits: int = 0
    misses: int = 0
    stale: int = 0
    changed: int = 0
    deleted: int = 0
    fresh_extracted: int = 0
    saved_entries: int = 0
    load_error: str = ""
    failure_stage: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def format_cache_stats(stats: InventoryCacheStats) -> list[str]:
    """Return human-readable inventory cache diagnostics."""
    path = stats.path or "(none)"
    lines = [
        "",
        "Cache:",
        f"  status: {stats.status}",
        f"  enabled: {str(stats.enabled).lower()}",
        f"  path: {path}",
        (
            "  entries: "
            f"{stats.hits} hit(s), {stats.misses} miss(es), "
            f"{stats.changed} changed, {stats.stale} stale, {stats.deleted} deleted"
        ),
        (
            "  extraction: "
            f"{stats.fresh_extracted} fresh file(s), {stats.saved_entries} saved entries"
        ),
    ]
    if stats.load_error:
        lines.append(f"  note: {stats.load_error}")
    return lines


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _hash_json(value: Any) -> str:
    return _sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _hash_file(path: Path) -> str | None:
    try:
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return "sha256:" + hasher.hexdigest()
    except OSError:
        return None


def hash_source_file(source_file: SourceFile) -> str | None:
    """Return a content hash for a source file, or None when unreadable."""
    return _hash_file(source_file.abs_path)


def _hash_labeled_files(paths: list[tuple[str, Path]]) -> str:
    hasher = hashlib.sha256()
    for label, path in sorted(paths, key=lambda item: item[0]):
        hasher.update(label.replace("\\", "/").encode("utf-8"))
        hasher.update(b"\0")
        try:
            hasher.update(path.read_bytes())
        except OSError:
            hasher.update(b"<unreadable>")
        hasher.update(b"\0")
    return "sha256:" + hasher.hexdigest()


def _path_has_excluded_part(path: Path) -> bool:
    return not EXCLUDED_DIRS.isdisjoint(path.parts) or is_agent_worktree_path(path)


def _gitignore_fingerprint(root: Path) -> str:
    paths: list[tuple[str, Path]] = []
    if root.exists():
        for gitignore in sorted(root.rglob(".gitignore")):
            try:
                rel = gitignore.relative_to(root)
            except ValueError:
                continue
            if _path_has_excluded_part(rel):
                continue
            paths.append((rel.as_posix(), gitignore))
    return _hash_labeled_files(paths)


def _implementation_fingerprint() -> str:
    package_root = Path(__file__).resolve().parents[1]
    rel_paths = [
        "extractors/common.py",
        "extractors/fastapi_contracts.py",
        "extractors/python_contracts.py",
        "extractors/python_extractor.py",
        "extractors/python_bindings.py",
        "extractors/ts_extractor.py",
        "extractors/go_extractor.py",
        "extractors/rust_extractor.py",
        "extractors/haskell_extractor.py",
        "extractors/ts_scripts/extract.js",
        "extractors/ts_scripts/package.json",
        "extractors/go_scripts/main.go",
        "extractors/go_scripts/go.mod",
        "extractors/haskell_scripts/Main.hs",
        "services/imports.py",
        "services/python_imports.py",
        "services/python_calls.py",
        "services/python_stdlib.py",
        "services/packages.py",
        "services/python_observations.py",
        "services/extraction_service.py",
        "extractors/haskell_scripts/Inventory.hs",
        "extractors/haskell_scripts/Parser.hs",
        "extractors/haskell_scripts/Paths.hs",
        "extractors/haskell_scripts/Json.hs",
        "extractors/rust_scripts/Cargo.toml",
        "extractors/rust_scripts/Cargo.lock",
        "extractors/rust_scripts/src/main.rs",
    ]
    return _hash_labeled_files(
        [
            (rel_path, package_root / rel_path)
            for rel_path in rel_paths
            if (package_root / rel_path).exists()
        ]
    )


def _plugin_fingerprint(root: Path) -> str:
    paths: list[tuple[str, Path]] = []
    plugin_lock = lock_path(root)
    if plugin_lock.exists():
        paths.append((plugin_lock.relative_to(root).as_posix(), plugin_lock))

    store = plugin_store(root)
    if store.exists():
        for path in sorted(store.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(root)
            if _path_has_excluded_part(rel):
                continue
            paths.append((rel.as_posix(), path))
    return _hash_labeled_files(paths)


def _filter_fingerprint() -> str:
    return _hash_json(
        {
            "excluded_dirs": sorted(EXCLUDED_DIRS),
            "agent_worktree_dir_patterns": AGENT_WORKTREE_DIR_PATTERNS,
            "language_extensions": LANGUAGE_EXTENSIONS,
            "dockerfile_patterns": DOCKERFILE_PATTERNS,
            "compose_patterns": COMPOSE_PATTERNS,
        }
    )


def build_inventory_cache_key(
    src_dir: str | Path,
    source_snapshot: SourceSnapshot,
    *,
    deep: bool,
    include_empty: bool,
    extractor_registry: dict[str, str],
) -> dict[str, Any]:
    """Build cache metadata that must match before entries are reused."""
    project_root = Path.cwd().resolve()
    return {
        "version": CACHE_VERSION,
        "schema": CACHE_SCHEMA,
        "llm_wiki_version": LLM_WIKI_VERSION,
        "src_dir": str(Path(src_dir).resolve()),
        "deep": bool(deep),
        "include_empty": bool(include_empty),
        "python_version": ".".join(str(part) for part in sys.version_info[:3]),
        "extractor_registry": dict(sorted(extractor_registry.items())),
        "extractor_fingerprint": _implementation_fingerprint(),
        "filter_fingerprint": _filter_fingerprint(),
        "gitignore_fingerprint": source_snapshot.gitignore_fingerprint,
        "source_selection_identity": source_snapshot.source_selection_identity,
        "plugin_lock_fingerprint": _plugin_fingerprint(project_root),
    }


def _resolve_gitdir_file(git_file: Path) -> Path | None:
    try:
        text = git_file.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    prefix = "gitdir:"
    if not text.lower().startswith(prefix):
        return None
    raw_path = text[len(prefix) :].strip()
    gitdir = Path(raw_path)
    if not gitdir.is_absolute():
        gitdir = git_file.parent / gitdir
    return gitdir.resolve()


def _nearest_git_dir(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        dot_git = candidate / ".git"
        if dot_git.is_dir():
            return dot_git
        if dot_git.is_file():
            gitdir = _resolve_gitdir_file(dot_git)
            if gitdir is not None:
                return gitdir
    return None


def resolve_inventory_cache_path(
    src_dir: str | Path,
    cache_dir: str | None = None,
    *,
    env: dict[str, str] | None = None,
) -> Path | None:
    """Resolve the cache file path for a source tree and optional override."""
    env_map = env if env is not None else os.environ
    configured_dir = cache_dir or env_map.get(ENV_CACHE_DIR)
    if configured_dir:
        base = Path(configured_dir).expanduser()
        if not base.is_absolute():
            base = Path.cwd() / base
        return base.resolve() / CACHE_FILENAME

    git_dir = _nearest_git_dir(Path(src_dir))
    if git_dir is None:
        return None
    return git_dir / CACHE_FILENAME


def cache_options_from_args(args) -> InventoryCacheOptions:
    disabled = bool(getattr(args, "no_cache", False))
    rebuild = bool(getattr(args, "rebuild_cache", False))
    cache_dir = getattr(args, "cache_dir", None)
    if cache_dir is not None and not str(cache_dir).strip():
        raise RuntimeOutputError("--cache-dir must be a non-empty directory path")
    if disabled and (rebuild or cache_dir is not None):
        raise RuntimeOutputError(
            "--no-cache cannot be combined with --cache-dir or --rebuild-cache"
        )
    return InventoryCacheOptions(
        enabled=not disabled,
        rebuild=rebuild,
        cache_dir=cache_dir,
        stats_enabled=bool(getattr(args, "cache_stats", False)),
        warning=stderr_warning,
    )


def prepare_cache_options(
    src_dir: str | Path, options: InventoryCacheOptions | None
) -> InventoryCacheOptions | None:
    if options is None or not options.enabled or options.destination is not None:
        return options
    explicit = options.cache_dir is not None or bool(os.environ.get(ENV_CACHE_DIR))
    try:
        path = resolve_inventory_cache_path(src_dir, options.cache_dir)
    except (OSError, ValueError, RuntimeError) as exc:
        if explicit:
            raise RuntimeOutputError(
                f"Cannot resolve explicit cache destination: {exc}"
            ) from exc
        warn(
            options.warning,
            f"Implicit cache destination unavailable: {exc}. Use --cache-dir.",
        )
        return replace(
            options, destination=RuntimeDestination(None, False, "failed", str(exc))
        )
    return replace(
        options,
        destination=prepare_destination(
            path, kind="cache", explicit=explicit, warning=options.warning
        ),
    )


class InventoryCache:
    """JSON-backed cache for per-file built-in inventory entries."""

    def __init__(self, src_dir: str | Path, options: InventoryCacheOptions):
        options = prepare_cache_options(src_dir, options) or options
        destination = options.destination
        path = destination.path if destination is not None else None
        enabled = bool(
            options.enabled
            and destination is not None
            and path is not None
            and destination.status != "failed"
        )
        self.path = path
        self.options = options
        self.stats = InventoryCacheStats(
            enabled=enabled,
            path=str(path) if path is not None else None,
            status="rebuild"
            if enabled and options.rebuild
            else ("miss" if enabled else "disabled"),
            load_error=destination.error or "" if destination is not None else "",
            failure_stage="preflight"
            if destination is not None and destination.status == "failed"
            else None,
        )

    @property
    def enabled(self) -> bool:
        return self.stats.enabled

    @observed_phase("cache_lookup")
    def load(self, cache_key: dict[str, Any]) -> dict[str, dict]:
        if not self.enabled or self.path is None:
            return {}
        if self.options.rebuild:
            return {}
        if not self.path.exists():
            self.stats.status = "miss"
            return {}

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.stats.status = "corrupt"
            self.stats.load_error = str(exc)
            self.stats.failure_stage = "load"
            warn(
                self.options.warning,
                f"Inventory cache could not be loaded: {exc}; extracting fresh inventory.",
            )
            return {}

        if not isinstance(raw, dict) or not isinstance(raw.get("files"), dict):
            self.stats.status = "corrupt"
            self.stats.load_error = "cache root must contain a files object"
            return {}

        expected = {key: raw.get(key) for key in cache_key}
        if expected != cache_key:
            self.stats.status = "invalid"
            self.stats.stale += len(raw.get("files", {}))
            return {}

        self.stats.status = "loaded"
        return raw["files"]

    def finalize_lookup_status(self) -> None:
        if not self.enabled:
            return
        if self.options.rebuild:
            self.stats.status = "rebuild"
            return
        if self.stats.status in {"corrupt", "invalid"}:
            return
        if self.stats.hits and not (
            self.stats.misses or self.stats.changed or self.stats.stale
        ):
            self.stats.status = "hit"
        elif self.stats.hits:
            self.stats.status = "partial"
        elif self.stats.misses or self.stats.changed or self.stats.stale:
            self.stats.status = "miss"

    @observed_phase("cache_save")
    def save(self, cache_key: dict[str, Any], files: dict[str, dict]) -> None:
        if not self.enabled or self.path is None:
            return
        payload = dict(cache_key)
        payload["files"] = dict(sorted(files.items()))
        try:
            write_json_atomic(self.path, payload)
            self.stats.saved_entries = len(files)
        except OSError as exc:
            self.stats.status = "save_failed"
            self.stats.load_error = str(exc)
            self.stats.failure_stage = "save"
            self.stats.saved_entries = 0
            warn(
                self.options.warning,
                f"Inventory cache was not saved at {self.path}: {exc}",
            )


def is_valid_cache_entry(entry: Any, source_file: SourceFile, file_hash: str) -> bool:
    if not isinstance(entry, dict):
        return False
    if entry.get("language") != source_file.language:
        return False
    if entry.get("hash") != file_hash:
        return False
    return isinstance(entry.get("inventory"), dict)


def make_cache_entry(
    source_file: SourceFile, file_hash: str, inventory_entry: dict
) -> dict:
    return {
        "language": source_file.language,
        "size": source_file.size,
        "mtime_ns": source_file.mtime_ns,
        "hash": file_hash,
        "inventory": inventory_entry,
    }
