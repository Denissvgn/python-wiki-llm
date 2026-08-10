"""Read-only classification for wiki bootstrap, sync, and migration routing."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Union

from ..config import AGENT_CHOICES
from .filesystem_guard import atomic_write_guarded_bytes, ensure_guarded_directory
from .io import first_unsafe_path_component, formatted_json_bytes
from .rendering_lifecycle import RenderReason
from .schema import SCHEMA_BLOCK_VERSION, SchemaRenderProfile
from .sync_manifest import MANIFEST_FILENAME
from .wiki_scaffold import (
    INITIAL_WIKI_INDEX_MARKDOWN,
    INITIAL_WIKI_LOG_MARKDOWN,
)
from .wiki_surface import iter_directory_kinds, iter_page_kinds


class WikiScaffoldPathError(ValueError):
    """Raised when a managed scaffold path is redirected or non-regular."""


@dataclass(frozen=True)
class WikiScaffoldProvision:
    """Additive scaffold entries created by one guarded provisioning pass."""

    directories: tuple[str, ...]
    gitkeeps: tuple[str, ...]
    files: tuple[str, ...]


def require_safe_wiki_scaffold(wiki_dir: Union[str, Path]) -> None:
    """Preflight every managed scaffold path before any lifecycle mutation."""

    root = Path(wiki_dir)
    directories = (root,) + tuple(
        root / entry.directory
        for entry in iter_directory_kinds()
        if entry.directory is not None
    )
    files = tuple(directory / ".gitkeep" for directory in directories) + (
        root / "index.md",
        root / "log.md",
    )
    for path in (*directories, *files):
        unsafe = first_unsafe_path_component(path)
        if unsafe is not None:
            raise WikiScaffoldPathError(
                f"wiki scaffold path contains unsafe component: {unsafe}"
            )
    for directory in directories:
        if directory.exists() and not directory.is_dir():
            raise WikiScaffoldPathError(
                f"wiki scaffold directory must be a regular directory: {directory}"
            )
    for path in files:
        if path.exists() and not path.is_file():
            raise WikiScaffoldPathError(
                f"wiki scaffold file must be a regular file: {path}"
            )


def provision_wiki_scaffold(wiki_dir: Union[str, Path]) -> WikiScaffoldProvision:
    """Create missing scaffold entries with no-follow, descriptor-pinned writes."""

    root = Path(wiki_dir)
    require_safe_wiki_scaffold(root)
    directories = (root,) + tuple(
        root / entry.directory
        for entry in iter_directory_kinds()
        if entry.directory is not None
    )
    created_directories: list[str] = []
    created_gitkeeps: list[str] = []
    created_files: list[str] = []

    def absolute(path: Path) -> Path:
        return path if path.is_absolute() else Path.cwd().resolve() / path

    try:
        for directory in directories:
            existed = directory.exists()
            ensure_guarded_directory(absolute(directory))
            if not existed:
                relative = directory.relative_to(root).as_posix()
                created_directories.append("./" if relative == "." else f"{relative}/")
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                atomic_write_guarded_bytes(
                    absolute(gitkeep),
                    b"",
                    mode=0o644,
                    expected_existing=None,
                )
                created_gitkeeps.append(gitkeep.relative_to(root).as_posix())

        for name, content in (
            ("index.md", INITIAL_WIKI_INDEX_MARKDOWN),
            ("log.md", INITIAL_WIKI_LOG_MARKDOWN),
        ):
            target = root / name
            if not target.exists():
                atomic_write_guarded_bytes(
                    absolute(target),
                    content.encode("utf-8"),
                    mode=0o644,
                    expected_existing=None,
                )
                created_files.append(name)
        require_safe_wiki_scaffold(root)
    except (OSError, UnicodeError, ValueError) as exc:
        raise WikiScaffoldPathError(
            f"wiki scaffold changed or could not be provisioned safely: {exc}"
        ) from exc
    return WikiScaffoldProvision(
        directories=tuple(created_directories),
        gitkeeps=tuple(created_gitkeeps),
        files=tuple(created_files),
    )


class WikiLifecycleState(str, Enum):
    """One unambiguous lifecycle route for a wiki target."""

    FIRST_USE = "first-use"
    SYNC_SEEDABLE = "sync-seedable"
    MIGRATION_REQUIRED = "migration-required"
    MANAGED = "managed"


def _uses_windows_command_line() -> bool:
    """Return whether lifecycle guidance should use Windows CLI quoting."""

    return os.name == "nt"


def _render_recovery_command(arguments: list[str]) -> str:
    """Render a copy-pasteable recovery command for the current platform."""

    if _uses_windows_command_line():
        return subprocess.list2cmdline(arguments)
    return shlex.join(arguments)


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
        entry.directory for entry in iter_page_kinds() if entry.directory is not None
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
                legacy_fields = {
                    "agent",
                    "quality_hints",
                    "reference_skill",
                    "issue_reporting",
                }
                profiled_fields = legacy_fields | {
                    "render_profile_version",
                    "render_reason",
                    "rendered_profile",
                }
                if (
                    not isinstance(config, dict)
                    or frozenset(config)
                    not in {frozenset(legacy_fields), frozenset(profiled_fields)}
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
                legacy_config = {
                    "agent": config["agent"],
                    "quality_hints": config["quality_hints"],
                    "reference_skill": config["reference_skill"],
                    "issue_reporting": config["issue_reporting"],
                }
                if set(config) == legacy_fields:
                    expected = (json.dumps(legacy_config, indent=2) + "\n").encode()
                else:
                    if (
                        config["rendered_profile"]
                        not in {profile.value for profile in SchemaRenderProfile}
                        or config["render_profile_version"] != SCHEMA_BLOCK_VERSION
                        or config["render_reason"]
                        not in {reason.value for reason in RenderReason}
                    ):
                        return False
                    expected = formatted_json_bytes(config)
                if raw_config.encode("utf-8") != expected:
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

    command = _render_recovery_command(
        ["llm-wiki", "bootstrap", "--src-dir", src_dir, "--wiki-dir", str(wiki_dir)]
    )
    return f"Run `{command}` to create the initial wiki and manifest."


def migration_guidance(*, src_dir: str, wiki_dir: Union[str, Path]) -> str:
    """Return a path-safe migration preview command."""

    command = _render_recovery_command(
        [
            "llm-wiki",
            "migrate",
            "--dry-run",
            "--src-dir",
            src_dir,
            "--wiki-dir",
            str(wiki_dir),
        ]
    )
    return f"Preview the existing wiki migration with `{command}`."


def sync_guidance(*, src_dir: str, wiki_dir: Union[str, Path]) -> str:
    """Return a path-safe manifest-seeding sync command."""

    command = _render_recovery_command(
        [
            "llm-wiki",
            "sync",
            "--jobs",
            "1",
            "--src-dir",
            src_dir,
            "--wiki-dir",
            str(wiki_dir),
        ]
    )
    return f"Seed the existing wiki safely with `{command}`."


__all__ = [
    "WikiScaffoldPathError",
    "WikiLifecycleState",
    "bootstrap_guidance",
    "classify_wiki_lifecycle",
    "is_pristine_wiki_target",
    "migration_guidance",
    "require_safe_wiki_scaffold",
    "sync_guidance",
]
