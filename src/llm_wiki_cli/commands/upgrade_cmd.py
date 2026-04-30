"""llm-wiki upgrade — refresh all framework-managed artifacts in place.

Replaces the uninstall → init → install-hook cycle with a single idempotent
command that:
1. Replaces the agent constraint block with the latest version
2. Ensures wiki directory structure is complete
3. Reinstalls git hooks
4. Updates .gitignore entries
5. Optionally switches agents
"""

from __future__ import annotations

import os
import shutil
import stat
import sys
from pathlib import Path

from ..config import AGENT_CHOICES, CLI_AGENTS, DEFAULT_WIKI_DIR, IDE_AGENTS, get_agent_config_path, read_config, validate_path, write_config
from ..services.io import read_md, write_md
from ..services.schema import (
    ALL_SCHEMA_FILES,
    CONSTRAINT_START,
    SCHEMA_FILENAMES,
    build_schema_content,
    refresh_skill_blocks,
    replace_schema_block,
    strip_skill_blocks,
    strip_wiki_block,
)

# Re-use hook builders from hook_cmd to avoid duplication
from .hook_cmd import _build_ide_post_commit, _build_post_commit, _install_hook

_GITIGNORE_ENTRIES = [
    ".git/llm-wiki-prompt.txt",
    ".git/llm-wiki.lock",
    ".git/llm-wiki-breaker.json",
    ".git/llm-wiki-sync.log",
    ".git/llm-wiki-metrics.jsonl",
    ".git/llm-wiki-ci-report.md",
]


def _read_agent_config(wiki_dir: str) -> str | None:
    """Read the agent name persisted by `llm-wiki init`."""
    config = read_config(wiki_dir)
    agent = config.get("agent")
    if agent and agent != "generic":
        return agent
    # Check if config file actually exists (defaults return "generic")
    config_path = get_agent_config_path(wiki_dir)
    if config_path.exists():
        return agent
    return None


def _resolve_agent(args, wiki_dir: str) -> str:
    """Resolve agent: CLI --agent flag > persisted config > error."""
    agent = getattr(args, "agent", None)
    if agent:
        return agent

    stored = _read_agent_config(wiki_dir)
    if stored:
        return stored

    print(
        "Error: Cannot determine agent.\n"
        f"  No --agent flag provided and no config found at .git/.llm-wiki-agent\n\n"
        "  Either run `llm-wiki init --agent <agent>` first,\n"
        "  or pass --agent to this command:\n"
        f"    llm-wiki upgrade --agent <{'|'.join(AGENT_CHOICES)}>",
        file=sys.stderr,
    )
    sys.exit(1)


def _upgrade_schema(agent: str, wiki_dir: str, old_agent: str | None, *, quality_hints: bool = True) -> str:
    """Replace or migrate the agent schema constraint block.

    Returns a summary message.
    """
    new_content = build_schema_content(agent, wiki_dir, quality_hints=quality_hints)
    new_filename = SCHEMA_FILENAMES.get(agent)

    if old_agent and old_agent != agent:
        # Switching agents — clean old schema file first
        old_filename = SCHEMA_FILENAMES.get(old_agent)
        if old_filename:
            old_path = Path(old_filename)
            if old_path.exists():
                existing = read_md(old_path)
                if CONSTRAINT_START in existing:
                    stripped = strip_skill_blocks(strip_wiki_block(existing))
                    if stripped:
                        write_md(old_path, stripped)
                        print(f"  Cleaned constraint block from: {old_filename}")
                    else:
                        old_path.unlink()
                        print(f"  Removed: {old_filename} (only contained wiki constraints)")

    # Write latest block to the target schema file
    if new_filename:
        schema_path = Path(new_filename)
        replace_schema_block(schema_path, new_content)
        return new_filename
    return "(no schema file)"


def _upgrade_dirs(wiki_dir: str) -> int:
    """Ensure all standard wiki subdirectories exist. Returns count of newly created dirs."""
    base = Path(wiki_dir)
    subdirs = ["entities", "modules", "workflows", "infrastructure"]
    created = 0
    for name in ["."] + subdirs:
        d = base if name == "." else base / name
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created += 1
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
    # Ensure core files exist
    index_path = base / "index.md"
    if not index_path.exists():
        write_md(index_path,
            "# LLM Wiki Index\n\nCatalog of project modules and entities.\n\n"
            "## Entities\n\n## Modules\n\n## Workflows\n\n## Infrastructure\n"
        )
        created += 1
    log_path = base / "log.md"
    if not log_path.exists():
        write_md(log_path, "# Architectural Log\n\nAppend-only chronological log.\n\n")
        created += 1
    return created


def _upgrade_hooks(agent: str, wiki_dir: str) -> None:
    """Reinstall git hooks for the resolved agent."""
    git_dir = Path(".git")
    if not git_dir.exists():
        print("  Skipped hooks (no .git directory)")
        return

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    if agent in IDE_AGENTS:
        _install_hook(hooks_dir, "post-commit", _build_ide_post_commit(wiki_dir))
        print(f"  Hooks: IDE prompt-generation mode ({agent})")
    else:
        _install_hook(hooks_dir, "post-commit", _build_post_commit(agent))
        print(f"  Hooks: CLI auto-sync mode ({agent})")


def _upgrade_gitignore() -> int:
    """Add any missing llm-wiki temp file entries to .gitignore. Returns count added."""
    gitignore = Path(".gitignore")
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    to_add = [e for e in _GITIGNORE_ENTRIES if e not in existing]
    if to_add:
        with open(gitignore, "a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("# LLM Wiki temp files\n")
            for entry in to_add:
                f.write(entry + "\n")
    return len(to_add)


def run(args):
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(wiki_dir, "--wiki-dir")

    agent = _resolve_agent(args, wiki_dir)
    old_agent = _read_agent_config(wiki_dir)
    switching = old_agent and old_agent != agent

    # Resolve quality_hints: CLI flag > stored config > default (True)
    cli_hints = getattr(args, "quality_hints", None)
    if cli_hints is not None:
        quality_hints = cli_hints
    else:
        stored = read_config(wiki_dir)
        quality_hints = stored.get("quality_hints", True)

    print("LLM Wiki Upgrade")
    print("=" * 40)

    if switching:
        print(f"\n  Switching agent: {old_agent} → {agent}")
    else:
        print(f"\n  Agent: {agent}")

    # 1. Schema constraint block
    print("\n1. Agent Schema:")
    schema_file = _upgrade_schema(agent, wiki_dir, old_agent, quality_hints=quality_hints)
    print(f"  Updated: {schema_file}")
    refreshed_skills = refresh_skill_blocks(agent, wiki_dir)
    if refreshed_skills:
        print(f"  Refreshed {len(refreshed_skills)} plugin skill block(s)")

    # 2. Wiki directories
    print("\n2. Wiki Structure:")
    new_dirs = _upgrade_dirs(wiki_dir)
    if new_dirs:
        print(f"  Created {new_dirs} new entries in {wiki_dir}/")
    else:
        print(f"  All directories present in {wiki_dir}/")

    # 3. Git hooks
    print("\n3. Git Hooks:")
    _upgrade_hooks(agent, wiki_dir)

    # 4. .gitignore
    print("\n4. .gitignore:")
    added = _upgrade_gitignore()
    if added:
        print(f"  Added {added} entries")
    else:
        print("  Already up to date")

    # 5. Persist agent config
    write_config(wiki_dir, {"agent": agent, "quality_hints": quality_hints})

    # Warn if CLI agent executable missing
    executable = CLI_AGENTS.get(agent)
    if executable and not shutil.which(executable):
        print(
            f"\nWarning: '{executable}' not found on PATH.\n"
            f"  Background auto-sync won't work until '{executable}' is installed."
        )

    print("\nUpgrade complete.")
