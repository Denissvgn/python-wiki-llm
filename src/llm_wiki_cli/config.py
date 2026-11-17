"""Shared constants and utilities for agent-wiki-cli."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .services.filesystem_guard import (
    atomic_write_private_bytes,
    ensure_guarded_directory,
)
from .services.io import first_unsafe_path_component
from llm_wiki_engine.knowledge_evidence import formatted_json_bytes
from .services.path_policy import (  # noqa: F401  (re-exported)
    DEFAULT_WIKI_DIR,
    EXCLUDED_DIRS,
    AGENT_WORKTREE_DIR_PATTERNS,
    _normalized_rel_parts,
    is_agent_worktree_path,
    PathValidationError,
    validate_path,
    validate_source_root,
    validate_source_paths,
)
from .services.gitignore import (  # noqa: F401  (re-exported)
    _GitignoreRule,
    GitIgnoreMatcher,
    _normalize_gitignore_trailing_spaces,
    _parse_gitignore_text,
    _parse_gitignore_file,
    _match_gitignore_pattern,
    _rule_matches,
    build_gitignore_matcher,
    is_ignored_by_gitignore,
)
from .services.extractor_registry import (  # noqa: F401  (re-exported)
    DOCKERFILE_PATTERNS,
    COMPOSE_PATTERNS,
    EXTRACTOR_REGISTRY,
)


AGENT_CHOICES = ["claude", "cursor", "copilot", "aider", "opencode", "generic"]

# Agents that have a real CLI executable (key=agent name, value=executable)
CLI_AGENTS: dict[str, str] = {
    "claude": "claude",
    "aider": "aider",
    "opencode": "opencode",
}

# Agents that are IDE-only and cannot run headlessly
IDE_AGENTS: set[str] = {"cursor", "copilot", "generic"}


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
