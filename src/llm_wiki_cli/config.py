"""Shared constants and utilities for agent-wiki-cli."""

from __future__ import annotations

import json
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

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

    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    resolved = candidate.resolve()
    if not resolved.is_dir():
        raise PathValidationError(
            f"Error: {label} '{path}' resolves to '{resolved}', "
            "which is not an existing directory."
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
}


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


def _parse_gitignore_file(gitignore_path: Path, base: str = "") -> list[_GitignoreRule]:
    rules: list[_GitignoreRule] = []
    if not gitignore_path.exists():
        return rules

    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n\r")
                line = _normalize_gitignore_trailing_spaces(line)
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
    except OSError:
        pass
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


def read_config(wiki_dir: "str | Path") -> dict:
    """Read the persisted llm-wiki config as a dict.

    Handles backward compatibility: if the file contains a bare agent name
    string (pre-v0.3 format), it is treated as ``{"agent": "<value>", "quality_hints": true}``.

    Returns *_DEFAULT_CONFIG* values for any missing keys.
    """
    config_path = get_agent_config_path(wiki_dir)
    if not config_path.exists():
        return dict(_DEFAULT_CONFIG)

    raw = config_path.read_text(encoding="utf-8").strip()

    # Backward compat: bare string = old format (just the agent name)
    if not raw.startswith("{"):
        result = dict(_DEFAULT_CONFIG)
        result["agent"] = raw
        return result

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Corrupted file — treat as defaults
        result = dict(_DEFAULT_CONFIG)
        return result

    # Fill in any missing keys from defaults
    for key, default in _DEFAULT_CONFIG.items():
        data.setdefault(key, default)
    return data


def write_config(wiki_dir: "str | Path", data: dict) -> None:
    """Persist the llm-wiki config dict to the agent config file."""
    config_path = get_agent_config_path(wiki_dir)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
