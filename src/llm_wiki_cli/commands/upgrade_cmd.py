"""llm-wiki upgrade — refresh all framework-managed artifacts in place.

Replaces the uninstall → init → install-hook cycle with a single idempotent
command that:
1. Replaces the agent constraint block with the latest version
2. Ensures wiki directory structure is complete
3. Reinstalls git hooks
4. Optionally switches agents
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from ..config import (
    AGENT_CHOICES,
    CLI_AGENTS,
    DEFAULT_WIKI_DIR,
    get_agent_config_path,
    read_config,
    validate_path,
    write_config,
)
from ..services.io import read_md, write_md
from ..services.schema import (
    CONSTRAINT_START,
    SCHEMA_FILENAMES,
    build_schema_content,
    refresh_skill_blocks,
    replace_schema_block,
    strip_skill_blocks,
    strip_wiki_block,
)
from ..services.skills import (
    REFERENCE_SKILL_ID,
    SkillsError,
    install_reference_skill,
    reference_skill_state,
    skills_install_dir,
)
from ..services.wiki_surface import iter_directory_kinds

# Re-use hook builders from hook_cmd to avoid duplication
from .hook_cmd import _build_ide_post_commit, _install_hook


@dataclass(frozen=True)
class StructureUpgradeResult:
    """Paths created while refreshing the framework-owned wiki structure."""

    directories: tuple[str, ...]
    gitkeeps: tuple[str, ...]
    files: tuple[str, ...]

    @property
    def created_count(self) -> int:
        return len(self.directories) + len(self.gitkeeps) + len(self.files)


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


def _upgrade_schema(
    agent: str, wiki_dir: str, old_agent: str | None, *, quality_hints: bool = True
) -> str:
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
                        print(
                            f"  Removed: {old_filename} (only contained wiki constraints)"
                        )

    # Write latest block to the target schema file
    if new_filename:
        schema_path = Path(new_filename)
        replace_schema_block(schema_path, new_content)
        return new_filename
    return "(no schema file)"


def _migrate_reference_skill(old_agent: str | None, new_agent: str) -> None:
    """Move the wiki-reference skill when an agent switch changes its home.

    Only an unmodified copy at the old location is removed; local edits are
    left in place and reported.
    """
    old_dir = skills_install_dir(old_agent)
    if old_dir == skills_install_dir(new_agent):
        return
    state = reference_skill_state(target=old_dir)
    if state == "unmodified":
        shutil.rmtree(old_dir / REFERENCE_SKILL_ID)
        print(f"  Removed {REFERENCE_SKILL_ID} skill from {old_dir}/ (relocating)")
    elif state == "modified":
        print(
            f"  Kept {REFERENCE_SKILL_ID} skill in {old_dir}/ "
            "(locally modified — remove manually if unwanted)"
        )


def _upgrade_dirs(wiki_dir: str) -> StructureUpgradeResult:
    """Ensure all standard wiki subdirectories and tracking files exist."""
    base = Path(wiki_dir)
    subdirs = [
        entry.directory
        for entry in iter_directory_kinds()
        if entry.directory is not None
    ]
    created_dirs: list[str] = []
    created_gitkeeps: list[str] = []
    created_files: list[str] = []
    for name in ["."] + subdirs:
        d = base if name == "." else base / name
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created_dirs.append("./" if name == "." else f"{name}/")
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            rel = ".gitkeep" if name == "." else f"{name}/.gitkeep"
            created_gitkeeps.append(rel)
    # Ensure core files exist
    index_path = base / "index.md"
    if not index_path.exists():
        write_md(
            index_path,
            "# LLM Wiki Index\n\nCatalog of project modules and entities.\n\n"
            "## Entities\n\n## Modules\n\n## Workflows\n\n## Infrastructure\n",
        )
        created_files.append("index.md")
    log_path = base / "log.md"
    if not log_path.exists():
        write_md(log_path, "# Architectural Log\n\nAppend-only chronological log.\n\n")
        created_files.append("log.md")
    return StructureUpgradeResult(
        directories=tuple(created_dirs),
        gitkeeps=tuple(created_gitkeeps),
        files=tuple(created_files),
    )


def _upgrade_hooks(agent: str, wiki_dir: str, *, force: bool = False) -> None:
    """Reinstall git hooks for the resolved agent."""
    git_dir = Path(".git")
    if not git_dir.exists():
        print("  Skipped hooks (no .git directory)")
        return

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    _install_hook(
        hooks_dir, "post-commit", _build_ide_post_commit(wiki_dir), force=force
    )
    print(f"  Hooks: prompt-generation mode ({agent})")


def run(args):
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(wiki_dir, "--wiki-dir")

    agent = _resolve_agent(args, wiki_dir)
    old_agent = _read_agent_config(wiki_dir)
    switching = old_agent and old_agent != agent

    # Resolve quality_hints and reference-skill refresh:
    # CLI flag > stored config > default (True)
    stored = read_config(wiki_dir)
    cli_hints = getattr(args, "quality_hints", None)
    if cli_hints is not None:
        quality_hints = cli_hints
    else:
        quality_hints = stored.get("quality_hints", True)
    cli_skills = getattr(args, "skills", None)
    if cli_skills is not None:
        reference_skill = cli_skills
    else:
        reference_skill = stored.get("reference_skill", True)

    print("LLM Wiki Upgrade")
    print("=" * 40)

    if switching:
        print(f"\n  Switching agent: {old_agent} → {agent}")
    else:
        print(f"\n  Agent: {agent}")

    # 1. Schema constraint block
    print("\n1. Agent Schema:")
    schema_file = _upgrade_schema(
        agent, wiki_dir, old_agent, quality_hints=quality_hints
    )
    print(f"  Updated: {schema_file}")
    refreshed_skills = refresh_skill_blocks(agent, wiki_dir)
    if refreshed_skills:
        print(f"  Refreshed {len(refreshed_skills)} plugin skill block(s)")
    if reference_skill:
        if switching:
            _migrate_reference_skill(old_agent, agent)
        # The constraint block points at this skill; keep its content in
        # lockstep with the installed CLI version.
        try:
            report = install_reference_skill(agent=agent, force=True)
        except SkillsError as exc:
            print(f"  Warning: could not refresh {REFERENCE_SKILL_ID} skill: {exc}")
        else:
            print(f"  Refreshed {REFERENCE_SKILL_ID} skill in {report.dest_dir}/")
    else:
        print(f"  Skipped {REFERENCE_SKILL_ID} skill refresh (opted out)")

    # 2. Wiki directories
    print("\n2. Wiki Structure:")
    structure_result = _upgrade_dirs(wiki_dir)
    if structure_result.created_count:
        print(f"  Created {structure_result.created_count} new entries in {wiki_dir}/")
        for rel in structure_result.directories:
            print(f"  Created directory: {rel}")
        for rel in structure_result.gitkeeps:
            print(f"  Created .gitkeep: {rel}")
        for rel in structure_result.files:
            print(f"  Created file: {rel}")
    else:
        print(f"  All directories present in {wiki_dir}/")

    # 3. Git hooks
    print("\n3. Git Hooks:")
    _upgrade_hooks(agent, wiki_dir, force=getattr(args, "force", False))

    # 4. Persist agent config
    write_config(
        wiki_dir,
        {
            "agent": agent,
            "quality_hints": quality_hints,
            "reference_skill": reference_skill,
        },
    )

    # Warn if CLI agent executable missing
    executable = CLI_AGENTS.get(agent)
    if executable and not shutil.which(executable):
        print(
            f"\nWarning: '{executable}' not found on PATH.\n"
            f"  Manual `llm-wiki trigger-agent --agent {agent}` won't work until "
            f"'{executable}' is installed."
        )

    print("\nUpgrade complete.")
