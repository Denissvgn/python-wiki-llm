"""Shared constants and utilities for agent-wiki-cli."""

from __future__ import annotations

import json
import os
import sys
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from fnmatch import fnmatch
from pathlib import Path

from .services.filesystem_guard import (
    WindowsSecurityGuardError,
    atomic_write_private_bytes,
    ensure_guarded_directory,
    windows_current_user_sid,
    windows_path_owner_sid,
)
from .services.io import first_unsafe_path_component
from .services.knowledge_evidence import formatted_json_bytes

DEFAULT_WIKI_DIR = "docs/llm_wiki"

# Directories excluded from source-file scans.  This intentionally covers both
# conventional environment names (``.venv``) and environment internals
# (``site-packages``) so renamed virtualenvs still stay out of the wiki.
EXCLUDED_DIRS: set[str] = {
    ".cache",
    ".direnv",
    ".eggs",
    ".env",
    ".git",
    ".mypy_cache",
    ".next",
    ".nox",
    ".npm",
    ".nuxt",
    ".parcel-cache",
    ".pnpm-store",
    ".pyre",
    ".pytest_cache",
    ".ruff_cache",
    ".svelte-kit",
    ".tox",
    ".venv",
    ".virtualenv",
    ".vite",
    ".yarn",
    "__pycache__",
    "__pypackages__",
    "bower_components",
    "build",
    "coverage",
    "dist",
    "env",
    "htmlcov",
    "jspm_packages",
    "node_modules",
    "out",
    "site-packages",
    "target",
    "venv",
    "virtualenv",
}

AGENT_WORKTREE_DIR_PATTERNS: tuple[tuple[str, ...], ...] = ((".claude", "worktrees"),)


def _normalized_rel_parts(path: "str | Path") -> tuple[str, ...]:
    text = path.as_posix() if isinstance(path, Path) else str(path)
    text = text.replace("\\", "/").strip("/")
    return tuple(part for part in text.split("/") if part and part != ".")


def is_agent_worktree_path(path: "str | Path") -> bool:
    """Return whether *path* is inside a generated agent worktree subtree."""
    parts = _normalized_rel_parts(path)
    for pattern in AGENT_WORKTREE_DIR_PATTERNS:
        pattern_len = len(pattern)
        if pattern_len == 0 or len(parts) < pattern_len:
            continue
        for index in range(len(parts) - pattern_len + 1):
            if parts[index : index + pattern_len] == pattern:
                return True
    return False


AGENT_CHOICES = ["claude", "cursor", "copilot", "aider", "opencode", "generic"]

# Agents that have a real CLI executable (key=agent name, value=executable)
CLI_AGENTS: dict[str, str] = {
    "claude": "claude",
    "aider": "aider",
    "opencode": "opencode",
}

# Agents that are IDE-only and cannot run headlessly
IDE_AGENTS: set[str] = {"cursor", "copilot", "generic"}

# Docker file discovery patterns
DOCKERFILE_PATTERNS: list[str] = [
    "Dockerfile",
    "Dockerfile.*",
    "*.dockerfile",
]
COMPOSE_PATTERNS: list[str] = [
    "docker-compose.yml",
    "docker-compose.*.yml",
    "docker-compose.yaml",
    "docker-compose.*.yaml",
    "compose.yml",
    "compose.*.yml",
    "compose.yaml",
    "compose.*.yaml",
]


class PathValidationError(ValueError):
    """Raised when a user-provided path escapes the project root."""


def validate_path(path: str, label: str = "path") -> Path:
    """Ensure *path* resolves inside the current working directory.

    Raises PathValidationError with a clear message if the resolved path escapes the
    repository root (cwd).
    """
    if "\0" in path:
        raise PathValidationError(f"Error: {label} contains an embedded NUL character.")
    resolved = (Path.cwd() / path).resolve()
    cwd = Path.cwd().resolve()
    try:
        resolved.relative_to(cwd)
    except ValueError:
        raise PathValidationError(
            f"Error: {label} '{path}' resolves to '{resolved}', "
            f"which is outside the project root '{cwd}'."
        )
    return resolved


def validate_source_root(
    path: str,
    label: str = "--src-dir",
    *,
    allow_external: bool = False,
) -> Path:
    """Validate a source root according to the CLI source-read policy.

    By default this preserves :func:`validate_path` behaviour and rejects paths
    outside the current working directory.  When ``allow_external`` is true, the
    path may live outside cwd but must resolve to an existing directory.
    """
    if not allow_external:
        return validate_path(path, label)

    try:
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise PathValidationError(
            f"Error: {label} '{path}' cannot be resolved to an existing "
            f"directory: {exc}."
        ) from exc
    if not resolved.is_dir():
        raise PathValidationError(
            f"Error: {label} '{path}' resolves to '{resolved}', "
            "which is not an existing directory."
        )
    normalized_candidate = Path(os.path.abspath(candidate))
    if resolved != normalized_candidate:
        effective_uid: int | None = None
        trusted_owner: Callable[[Path], bool] | None = None
        ownership_is_verifiable = False
        if sys.platform == "win32":
            try:
                current_sid = windows_current_user_sid()
            except (OSError, RuntimeError, TypeError, ValueError):
                pass
            else:
                if isinstance(current_sid, str) and current_sid:
                    ownership_is_verifiable = True
                    trusted_windows_sids = {
                        current_sid,
                        "S-1-5-18",  # LocalSystem
                        "S-1-5-32-544",  # Built-in Administrators
                    }

                    def is_trusted_windows_owner(component: Path) -> bool:
                        return windows_path_owner_sid(component) in trusted_windows_sids

                    trusted_owner = is_trusted_windows_owner
        else:
            get_effective_uid = getattr(os, "geteuid", None)
            if callable(get_effective_uid):
                try:
                    derived_uid = get_effective_uid()
                except (OSError, RuntimeError, TypeError, ValueError):
                    pass
                else:
                    if (
                        isinstance(derived_uid, int)
                        and not isinstance(derived_uid, bool)
                        and derived_uid >= 0
                    ):
                        effective_uid = derived_uid
                        ownership_is_verifiable = True
        trusted_uids = {0, effective_uid} if effective_uid is not None else set()
        try:
            unsafe = first_unsafe_path_component(
                candidate,
                trusted_symlink_uids=trusted_uids,
                trusted_symlink_owner=trusted_owner,
            )
        except (OSError, RuntimeError, WindowsSecurityGuardError) as exc:
            raise PathValidationError(
                f"Error: {label} '{path}' traverses a symlink or reparse point "
                "whose ownership cannot be verified on this platform."
            ) from exc
        if unsafe is not None:
            if not ownership_is_verifiable:
                raise PathValidationError(
                    f"Error: {label} '{path}' traverses symlink or reparse point "
                    f"'{unsafe}' whose ownership cannot be verified on this "
                    "platform."
                )
            if sys.platform == "win32":
                raise PathValidationError(
                    f"Error: {label} '{path}' traverses symlink or reparse point "
                    f"'{unsafe}' not owned by the current Windows user, "
                    "LocalSystem, or Administrators."
                )
            raise PathValidationError(
                f"Error: {label} '{path}' traverses symlink or reparse point "
                f"'{unsafe}' not owned by the current user or root."
            )
        warnings.warn(
            f"external source root '{normalized_candidate}' resolves to '{resolved}'.",
            UserWarning,
            stacklevel=2,
        )
    return resolved


def validate_source_paths(
    src_dir: str | Path,
    paths: list[str] | tuple[str, ...] | None,
    label: str = "--paths",
) -> None:
    """Ensure requested source file paths stay inside *src_dir*.

    The extract CLI accepts paths relative to ``--src-dir``.  Absolute paths are
    tolerated only when they still resolve inside the source root.
    """
    if not paths:
        return

    root = Path(src_dir).resolve()
    for raw_path in paths:
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = root / candidate
        try:
            candidate.resolve().relative_to(root)
        except (OSError, ValueError):
            raise PathValidationError(
                f"Error: {label} '{raw_path}' resolves outside source root '{root}'."
            )


# Registry mapping language name → extractor entry point.
# Format: "module.path:ClassName"
# New extractors (TypeScript, Go, Rust, …) are registered here.
EXTRACTOR_REGISTRY: dict[str, str] = {
    "python": "llm_wiki_cli.extractors.python_extractor:PythonExtractor",
    "typescript": "llm_wiki_cli.extractors.ts_extractor:TypeScriptExtractor",
    "go": "llm_wiki_cli.extractors.go_extractor:GoExtractor",
    "rust": "llm_wiki_cli.extractors.rust_extractor:RustExtractor",
    "haskell": "llm_wiki_cli.extractors.haskell_extractor:HaskellExtractor",
}


def get_agent_config_path(wiki_dir: "str | Path") -> Path:
    """Return the local-only agent config file path.

    Stored at ``.git/.llm-wiki-agent`` so it is never committed and each
    developer on a shared repo can use their own preferred agent without
    affecting teammates.

    Falls back to ``wiki_dir/.llm-wiki-agent`` when not inside a git
    repository (e.g. bare CI environments or tests that don't init git).
    """
    if Path(".git").is_dir():
        return Path(".git") / ".llm-wiki-agent"
    return Path(wiki_dir) / ".llm-wiki-agent"


# Default config values for new installations.
_DEFAULT_CONFIG: dict[str, object] = {
    "agent": "generic",
    "quality_hints": True,
    "reference_skill": True,
    "issue_reporting": False,
}
_CONFIG_EXPECTATION_UNSET = object()


class AgentConfigState(str, Enum):
    """Compatibility classification for the local agent configuration."""

    ABSENT = "absent"
    VALID = "valid"
    LEGACY = "legacy"
    INVALID = "invalid"


@dataclass(frozen=True)
class AgentConfigInspection:
    """One safe configuration read with provenance for status reporting."""

    state: AgentConfigState
    reason: str
    path: Path
    data: dict[str, object]
    raw_bytes: bytes | None = None


_OPTIONAL_CONFIG_STRING_FIELDS = (
    "source_selection",
    "rendered_profile",
    "render_reason",
    "pending_cleanup_agent",
)
_RENDER_STATE_FIELDS = frozenset(
    {"rendered_profile", "render_profile_version", "render_reason"}
)
_PENDING_CLEANUP_FIELDS = frozenset(
    {"pending_cleanup_agent", "pending_cleanup_reference"}
)
_RENDER_PROFILE_VERSION = 1
_RENDER_PROFILES = frozenset({"compact", "expanded_inline"})
_RENDER_REASONS = frozenset(
    {
        "reference-current",
        "skills-disabled",
        "reference-absent",
        "reference-modified",
        "reference-incomplete",
        "package-missing",
        "install-error",
    }
)
_OPAQUE_CONFIG_REASONS = frozenset(
    {
        "config-path-unsafe",
        "config-path-not-regular",
        "config-unreadable",
        "invalid-config-encoding",
        "invalid-config-json",
        "invalid-legacy-agent-name",
        "config-must-be-an-object-with-string-keys",
        "multiple-agent-config-homes",
    }
)


@dataclass(frozen=True)
class _GitignoreRule:
    base: str
    pattern: str
    negated: bool
    directory_only: bool
    anchored: bool


class GitIgnoreMatcher:
    """Ordered gitignore matcher for repository scans.

    This supports the semantics the extractors need without reparsing the same
    .gitignore file for every source file: negation, root-anchored patterns,
    nested .gitignore files, directory-only rules, and common ``**`` patterns.
    """

    def __init__(self, rules: list[_GitignoreRule]):
        self._rules = rules

    def last_matching_rule(self, rel_path: str) -> _GitignoreRule | None:
        """Return the final gitignore rule that matches *rel_path*, if any."""
        rel_path = rel_path.replace("\\", "/").strip("/")
        last_rule: _GitignoreRule | None = None
        for rule in self._rules:
            if _rule_matches(rel_path, rule):
                last_rule = rule
        return last_rule

    def is_ignored(self, rel_path: str) -> bool:
        rule = self.last_matching_rule(rel_path)
        return rule is not None and not rule.negated


def _normalize_gitignore_trailing_spaces(line: str) -> str:
    """Remove Git-insignificant trailing spaces from one ignore pattern.

    Backslashes quote the next character, so escaped spaces are retained while
    an unescaped trailing run is removed.  Decode only quoted spaces here;
    broader gitignore escape and wildmatch semantics remain unchanged.  Tabs
    are intentionally untouched.
    """
    first_trailing_space: int | None = None
    index = 0
    while index < len(line):
        if line[index] == "\\":
            first_trailing_space = None
            index += 2
            continue
        if line[index] == " ":
            if first_trailing_space is None:
                first_trailing_space = index
        else:
            first_trailing_space = None
        index += 1

    if first_trailing_space is not None:
        line = line[:first_trailing_space]

    normalized: list[str] = []
    index = 0
    while index < len(line):
        if line[index] != "\\":
            normalized.append(line[index])
            index += 1
            continue

        run_start = index
        while index < len(line) and line[index] == "\\":
            index += 1
        backslash_count = index - run_start
        if index < len(line) and line[index] == " " and backslash_count % 2:
            normalized.append("\\" * (backslash_count - 1))
            normalized.append(" ")
            index += 1
            continue
        normalized.append("\\" * backslash_count)

    return "".join(normalized)


def _parse_gitignore_text(raw_text: str, base: str = "") -> list[_GitignoreRule]:
    """Parse already captured gitignore text without performing file I/O."""
    rules: list[_GitignoreRule] = []
    for raw in raw_text.splitlines():
        line = _normalize_gitignore_trailing_spaces(raw)
        if not line or line.startswith("#"):
            continue
        negated = line.startswith("!")
        if negated:
            line = line[1:]
        anchored = line.startswith("/")
        if anchored:
            line = line[1:]
        directory_only = line.endswith("/")
        line = line.rstrip("/")
        if line:
            rules.append(
                _GitignoreRule(
                    base=base.strip("/"),
                    pattern=line.replace("\\", "/"),
                    negated=negated,
                    directory_only=directory_only,
                    anchored=anchored,
                )
            )
    return rules


def _parse_gitignore_file(gitignore_path: Path, base: str = "") -> list[_GitignoreRule]:
    rules: list[_GitignoreRule] = []
    if not gitignore_path.exists():
        return rules

    try:
        return _parse_gitignore_text(
            gitignore_path.read_text(encoding="utf-8"),
            base,
        )
    except OSError:
        return rules


def _match_gitignore_pattern(
    rel_path: str, pattern: str, *, directory_only: bool = False
) -> bool:
    """Check if a relative path matches a gitignore pattern."""
    rel_path = rel_path.replace("\\", "/").strip("/")
    pattern = pattern.replace("\\", "/").strip("/")

    if not rel_path or not pattern:
        return False

    if directory_only:
        if "/" in pattern:
            return (
                rel_path == pattern
                or rel_path.startswith(pattern + "/")
                or fnmatch(rel_path, pattern + "/**")
            )
        parts = rel_path.split("/")
        return any(fnmatch(part, pattern) for part in parts[:-1])

    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return rel_path == prefix or rel_path.startswith(prefix + "/")

    if "/" in pattern:
        return fnmatch(rel_path, pattern) or fnmatch(rel_path, pattern + "/**")

    return any(fnmatch(part, pattern) for part in rel_path.split("/"))


def _rule_matches(rel_path: str, rule: _GitignoreRule) -> bool:
    if rule.base:
        if rel_path == rule.base:
            candidate = ""
        elif rel_path.startswith(rule.base + "/"):
            candidate = rel_path[len(rule.base) + 1 :]
        else:
            return False
    else:
        candidate = rel_path
    if not candidate:
        return False

    if rule.anchored:
        pattern = rule.pattern
        if rule.directory_only:
            return (
                candidate == pattern
                or candidate.startswith(pattern + "/")
                or fnmatch(candidate, pattern + "/**")
            )
        if "/" not in pattern:
            return "/" not in candidate and fnmatch(candidate, pattern)
        return fnmatch(candidate, pattern) or fnmatch(candidate, pattern + "/**")

    return _match_gitignore_pattern(
        candidate,
        rule.pattern,
        directory_only=rule.directory_only,
    )


def build_gitignore_matcher(root: "str | Path") -> GitIgnoreMatcher:
    """Parse root and nested .gitignore files once for a source scan."""
    root_path = Path(root)
    rules: list[_GitignoreRule] = []
    if not root_path.exists():
        return GitIgnoreMatcher(rules)

    for gitignore in sorted(root_path.rglob(".gitignore")):
        try:
            rel_parent = gitignore.parent.relative_to(root_path)
        except ValueError:
            continue
        if not EXCLUDED_DIRS.isdisjoint(rel_parent.parts) or is_agent_worktree_path(
            rel_parent
        ):
            continue
        base = "" if rel_parent == Path(".") else rel_parent.as_posix()
        rules.extend(_parse_gitignore_file(gitignore, base))
    return GitIgnoreMatcher(rules)


def is_ignored_by_gitignore(
    rel_path: str, gitignore_path: Path = Path(".gitignore")
) -> bool:
    """Check if a relative path is ignored according to one .gitignore file."""
    matcher = GitIgnoreMatcher(_parse_gitignore_file(gitignore_path, ""))
    return matcher.is_ignored(rel_path)


def inspect_config_path(config_path: "str | Path") -> AgentConfigInspection:
    """Inspect one exact local-agent config path without hiding its state.

    Known invalid fields fall back independently, unknown fields are retained,
    and callers receive a stable state/reason instead of having to infer
    provenance from the returned values.
    """
    config_path = Path(config_path)
    if first_unsafe_path_component(config_path) is not None:
        return AgentConfigInspection(
            AgentConfigState.INVALID,
            "config-path-unsafe",
            config_path,
            dict(_DEFAULT_CONFIG),
        )
    if not config_path.exists():
        return AgentConfigInspection(
            AgentConfigState.ABSENT,
            "config-not-present",
            config_path,
            dict(_DEFAULT_CONFIG),
        )
    if not config_path.is_file():
        return AgentConfigInspection(
            AgentConfigState.INVALID,
            "config-path-not-regular",
            config_path,
            dict(_DEFAULT_CONFIG),
        )

    try:
        raw_bytes = config_path.read_bytes()
        raw = raw_bytes.decode("utf-8").strip()
    except OSError:
        return AgentConfigInspection(
            AgentConfigState.INVALID,
            "config-unreadable",
            config_path,
            dict(_DEFAULT_CONFIG),
        )
    except UnicodeError:
        return AgentConfigInspection(
            AgentConfigState.INVALID,
            "invalid-config-encoding",
            config_path,
            dict(_DEFAULT_CONFIG),
        )

    # Backward compat: bare string = old format (just the agent name)
    if not raw.startswith("{"):
        result = dict(_DEFAULT_CONFIG)
        if raw in AGENT_CHOICES:
            result["agent"] = raw
            return AgentConfigInspection(
                AgentConfigState.LEGACY,
                "legacy-agent-name",
                config_path,
                result,
                raw_bytes,
            )
        return AgentConfigInspection(
            AgentConfigState.INVALID,
            "invalid-legacy-agent-name",
            config_path,
            result,
            raw_bytes,
        )

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeError):
        return AgentConfigInspection(
            AgentConfigState.INVALID,
            "invalid-config-json",
            config_path,
            dict(_DEFAULT_CONFIG),
            raw_bytes,
        )
    if not isinstance(data, dict) or any(not isinstance(key, str) for key in data):
        return AgentConfigInspection(
            AgentConfigState.INVALID,
            "config-must-be-an-object-with-string-keys",
            config_path,
            dict(_DEFAULT_CONFIG),
            raw_bytes,
        )

    normalized: dict[str, object] = dict(data)
    invalid_fields: list[str] = []
    raw_agent = normalized.get("agent")
    raw_agent_is_valid = isinstance(raw_agent, str) and raw_agent in AGENT_CHOICES

    # Fill in any missing keys from defaults
    for key, default in _DEFAULT_CONFIG.items():
        value = normalized.setdefault(key, default)
        if key == "agent":
            valid = isinstance(value, str) and value in AGENT_CHOICES
        else:
            valid = type(value) is bool
        if not valid:
            normalized[key] = default
            invalid_fields.append(key)

    for key in _OPTIONAL_CONFIG_STRING_FIELDS:
        if key not in normalized:
            continue
        value = normalized[key]
        if not isinstance(value, str) or not value:
            normalized.pop(key)
            invalid_fields.append(key)

    if (
        "pending_cleanup_agent" in normalized
        and normalized["pending_cleanup_agent"] not in AGENT_CHOICES
    ):
        normalized.pop("pending_cleanup_agent")
        invalid_fields.append("pending_cleanup_agent")
    if (
        "pending_cleanup_reference" in normalized
        and type(normalized["pending_cleanup_reference"]) is not bool
    ):
        normalized.pop("pending_cleanup_reference")
        invalid_fields.append("pending_cleanup_reference")
    present_cleanup_fields = _PENDING_CLEANUP_FIELDS.intersection(normalized)
    if present_cleanup_fields and present_cleanup_fields != _PENDING_CLEANUP_FIELDS:
        invalid_fields.extend(sorted(_PENDING_CLEANUP_FIELDS - present_cleanup_fields))
    elif (
        present_cleanup_fields
        and raw_agent_is_valid
        and normalized.get("pending_cleanup_agent") == raw_agent
    ):
        invalid_fields.append("pending_cleanup_agent")
        for field in _PENDING_CLEANUP_FIELDS:
            normalized.pop(field, None)

    if "render_profile_version" in normalized:
        version = normalized["render_profile_version"]
        if type(version) is not int or version < 1:
            normalized.pop("render_profile_version")
            invalid_fields.append("render_profile_version")

    present_render_fields = _RENDER_STATE_FIELDS.intersection(normalized)
    if present_render_fields and present_render_fields != _RENDER_STATE_FIELDS:
        invalid_fields.extend(sorted(_RENDER_STATE_FIELDS - present_render_fields))
        for field in _RENDER_STATE_FIELDS:
            normalized.pop(field, None)
    elif present_render_fields:
        invalid_render_fields: list[str] = []
        if normalized["rendered_profile"] not in _RENDER_PROFILES:
            invalid_render_fields.append("rendered_profile")
        if normalized["render_profile_version"] != _RENDER_PROFILE_VERSION:
            invalid_render_fields.append("render_profile_version")
        if normalized["render_reason"] not in _RENDER_REASONS:
            invalid_render_fields.append("render_reason")
        if invalid_render_fields:
            invalid_fields.extend(invalid_render_fields)
            for field in _RENDER_STATE_FIELDS:
                normalized.pop(field, None)

    state = AgentConfigState.INVALID if invalid_fields else AgentConfigState.VALID
    reason = (
        f"invalid-config-field:{sorted(set(invalid_fields))[0]}"
        if invalid_fields
        else "config-valid"
    )
    return AgentConfigInspection(state, reason, config_path, normalized, raw_bytes)


def inspect_config(wiki_dir: "str | Path") -> AgentConfigInspection:
    """Inspect the canonical config, adopting one safe legacy home if needed."""

    canonical = get_agent_config_path(wiki_dir)
    candidates: list[Path] = []
    seen: set[str] = set()
    for path in (
        canonical,
        Path(".git/.llm-wiki-agent"),
        Path(wiki_dir) / ".llm-wiki-agent",
    ):
        key = os.path.abspath(os.fspath(path))
        if key in seen:
            continue
        seen.add(key)
        if path.exists() or path.is_symlink():
            candidates.append(path)
    if len(candidates) > 1:
        return AgentConfigInspection(
            AgentConfigState.INVALID,
            "multiple-agent-config-homes",
            canonical,
            dict(_DEFAULT_CONFIG),
        )
    if candidates:
        return inspect_config_path(candidates[0])
    return inspect_config_path(canonical)


def config_requires_manual_recovery(inspection: AgentConfigInspection) -> bool:
    """Return whether config bytes must be inspected before lifecycle mutation."""

    if inspection.state is not AgentConfigState.INVALID:
        return False
    if inspection.reason in _OPAQUE_CONFIG_REASONS:
        return True
    return inspection.reason.startswith(
        "invalid-config-field:pending_cleanup"
    ) and not isinstance(inspection.data.get("pending_cleanup_agent"), str)


def read_config(wiki_dir: "str | Path") -> dict:
    """Return the backward-compatible config mapping used by older callers.

    Lifecycle commands should prefer :func:`inspect_config`, whose values are
    type-checked.  This adapter intentionally preserves unknown future agent
    names and known-field values just as the historical reader did, while
    retaining the new unsafe-path and malformed-file protections.
    """

    config_path = get_agent_config_path(wiki_dir)
    if first_unsafe_path_component(config_path) is not None or not config_path.exists():
        return dict(_DEFAULT_CONFIG)
    try:
        raw = config_path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return dict(_DEFAULT_CONFIG)
    if not raw.startswith("{"):
        result = dict(_DEFAULT_CONFIG)
        result["agent"] = raw
        return result
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeError):
        return dict(_DEFAULT_CONFIG)
    if not isinstance(data, dict):
        return dict(_DEFAULT_CONFIG)
    for key, default in _DEFAULT_CONFIG.items():
        data.setdefault(key, default)
    return data


def require_safe_config_path(wiki_dir: "str | Path") -> Path:
    """Return an absent or regular config path with no redirected component."""

    config_path = get_agent_config_path(wiki_dir)
    unsafe = first_unsafe_path_component(config_path)
    if unsafe is not None:
        raise PathValidationError(
            f"Error: agent config path contains unsafe component '{unsafe}'."
        )
    if config_path.exists() and not config_path.is_file():
        raise PathValidationError(
            "Error: agent config path must be absent or a regular file; "
            f"move aside '{config_path}' before retrying."
        )
    return config_path


def write_config(
    wiki_dir: "str | Path",
    data: dict,
    *,
    expected_existing: bytes | None | object = _CONFIG_EXPECTATION_UNSET,
) -> None:
    """Atomically persist config, optionally bound to an inspected snapshot."""

    config_path = require_safe_config_path(wiki_dir)
    absolute = (
        config_path if config_path.is_absolute() else Path.cwd().resolve() / config_path
    )
    ensure_guarded_directory(absolute.parent)
    payload = formatted_json_bytes(data)
    if expected_existing is _CONFIG_EXPECTATION_UNSET:
        atomic_write_private_bytes(absolute, payload)
    else:
        atomic_write_private_bytes(
            absolute,
            payload,
            expected_existing=expected_existing,
        )


def require_committed_config(wiki_dir: "str | Path", data: dict) -> None:
    """Require one canonical config home containing exactly the committed bytes."""

    expected = formatted_json_bytes(data)
    inspection = inspect_config(wiki_dir)
    canonical = get_agent_config_path(wiki_dir)
    if (
        inspection.state is not AgentConfigState.VALID
        or inspection.path != canonical
        or inspection.raw_bytes != expected
    ):
        raise PathValidationError(
            "Error: local agent config changed or another config home appeared "
            "after commit; inspect both config homes before continuing."
        )


def require_config_inspection_unchanged(
    wiki_dir: "str | Path",
    expected: AgentConfigInspection,
) -> None:
    """Require the exact config/home snapshot inspected before mutation."""

    current = inspect_config(wiki_dir)
    if (
        current.state is not expected.state
        or current.reason != expected.reason
        or current.path != expected.path
        or current.raw_bytes != expected.raw_bytes
    ):
        raise PathValidationError(
            "Error: local agent config changed after inspection; rerun the command "
            "after reviewing current intent and pending cleanup state."
        )
