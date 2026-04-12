"""Shared constants and utilities for llm-wiki-cli."""

from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_WIKI_DIR = "docs/llm_wiki"

# Directories excluded from all source-file scans (Python AST and Docker).
EXCLUDED_DIRS: set[str] = {
    "venv", ".venv", "env", ".env",
    ".tox", "node_modules", "__pycache__",
    ".eggs", "build", "dist", ".git",
}

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


def validate_path(path: str, label: str = "path") -> Path:
    """Ensure *path* resolves inside the current working directory.

    Raises SystemExit with a clear message if the resolved path escapes the
    repository root (cwd).
    """
    resolved = (Path.cwd() / path).resolve()
    cwd = Path.cwd().resolve()
    try:
        resolved.relative_to(cwd)
    except ValueError:
        print(
            f"Error: {label} '{path}' resolves to '{resolved}', "
            f"which is outside the project root '{cwd}'.",
            file=sys.stderr,
        )
        sys.exit(1)
    return resolved


# Registry mapping language name → extractor entry point.
# Format: "module.path:ClassName"
# New extractors (TypeScript, Go, Rust, …) are registered here.
EXTRACTOR_REGISTRY: dict[str, str] = {
    "python": "llm_wiki_cli.extractors.python_extractor:PythonExtractor",
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
