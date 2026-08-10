from __future__ import annotations

import shutil
import sys
from pathlib import Path

from ..config import (
    CLI_AGENTS,
    DEFAULT_WIKI_DIR,
    read_config,
    validate_path,
    write_config,
)
from ..services.io import read_md, write_md
from ..services.schema import (
    CONSTRAINT_START as _CONSTRAINT_START,
    SCHEMA_FILENAMES,
    build_schema_content as _build_schema_content,
    replace_schema_block,
)
from ..services.source_selection import (
    SourceSelectionError,
    resolve_source_selection,
)
from ..services.skills import (
    REFERENCE_SKILL_ID,
    SkillsError,
    install_reference_skill,
    list_bundled_skills,
)
from ..services.wiki_scaffold import (
    INITIAL_WIKI_INDEX_MARKDOWN,
    INITIAL_WIKI_LOG_MARKDOWN,
)
from ..services.wiki_surface import iter_directory_kinds


# Agents that have a real CLI executable for explicit trigger-agent use.
_CLI_AGENTS = CLI_AGENTS


def run(args):
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(wiki_dir, "--wiki-dir")
    stored = read_config(wiki_dir)
    requested_selection = getattr(args, "source_selection", None)
    stored_selection = stored.get("source_selection")
    if stored_selection is not None and not isinstance(stored_selection, str):
        print("Error: stored source_selection must be a string", file=sys.stderr)
        raise SystemExit(2)
    selection_override = (
        requested_selection
        if requested_selection is not None
        else stored_selection
    )
    try:
        selection_policy = resolve_source_selection(".", selection_override)
    except SourceSelectionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    source_selection = (
        selection_policy.path if selection_policy is not None else None
    )
    requested_agent = getattr(args, "agent", None)
    agent = requested_agent or str(stored.get("agent") or "generic")
    print(f"Initializing LLM Wiki with {agent} schema...")

    # Warn if the agent has a CLI executable that isn't installed
    executable = _CLI_AGENTS.get(agent)
    if executable and not shutil.which(executable):
        print(
            f"\nWarning: '{executable}' is not installed or not on PATH.\n"
            f"The schema file will be created, but manual agent execution\n"
            f"(`llm-wiki trigger-agent --agent {agent}`) will not work\n"
            f"until '{executable}' is installed.\n"
        )

    # 1. Create directory structure
    base_dir = Path(wiki_dir)
    directories = [base_dir]
    directories.extend(
        base_dir / entry.directory
        for entry in iter_directory_kinds()
        if entry.directory is not None
    )

    try:
        for d in directories:
            d.mkdir(parents=True, exist_ok=True)
            # Create empty .gitkeep so git tracks empty dirs
            (d / ".gitkeep").touch()
    except OSError as exc:
        print(f"Error creating wiki directories: {exc}")
        sys.exit(1)

    print(f"Created wiki directories in {base_dir}/")

    # 2. Create core files if they don't exist
    index_path = base_dir / "index.md"
    if not index_path.exists():
        write_md(index_path, INITIAL_WIKI_INDEX_MARKDOWN)

    log_path = base_dir / "log.md"
    if not log_path.exists():
        write_md(log_path, INITIAL_WIKI_LOG_MARKDOWN)

    # 3. Create or refresh the Agent Schema. Unspecified preferences preserve an
    # existing installation's choices; a new installation receives config defaults.
    cli_no_quality_hints = getattr(args, "no_quality_hints", None)
    if cli_no_quality_hints is None:
        quality_hints = bool(stored.get("quality_hints", True))
    else:
        quality_hints = not cli_no_quality_hints
    cli_issue_reporting = getattr(args, "issue_reporting", None)
    if cli_issue_reporting is None:
        issue_reporting = bool(stored.get("issue_reporting", False))
    else:
        issue_reporting = cli_issue_reporting
    filename = SCHEMA_FILENAMES.get(agent)
    if filename:
        schema_path = Path(filename)
        # ensure parent exists (e.g. for .github/)
        schema_path.parent.mkdir(parents=True, exist_ok=True)

        content_to_add = _build_schema_content(
            agent,
            wiki_dir,
            quality_hints=quality_hints,
            issue_reporting=issue_reporting,
            source_selection=source_selection,
        )

        if schema_path.exists():
            existing_content = read_md(schema_path)

            if _CONSTRAINT_START not in existing_content:
                write_md(schema_path, existing_content + "\n\n" + content_to_add)
                print(f"Appended agent constraints to existing file: {schema_path}")
            else:
                replace_schema_block(schema_path, content_to_add)
                print(f"Refreshed agent constraints in existing file: {schema_path}")
        else:
            write_md(schema_path, content_to_add)
            print(f"Created agent schema file: {schema_path}")

    # 4. Install the CLI-owned wiki-reference skill that the constraint
    # block's deep-reference pointers target
    cli_no_skills = getattr(args, "no_skills", None)
    if cli_no_skills is None:
        install_skill = bool(stored.get("reference_skill", True))
    else:
        install_skill = not cli_no_skills
    if install_skill:
        try:
            report = install_reference_skill(agent=agent)
        except SkillsError as exc:
            print(f"Warning: could not install {REFERENCE_SKILL_ID} skill: {exc}")
        else:
            if report.ok:
                print(f"Installed {REFERENCE_SKILL_ID} skill in {report.dest_dir}/")
            else:
                print(
                    f"Kept existing {REFERENCE_SKILL_ID} skill tree in "
                    f"{report.dest_dir}/ (not an exact bundled copy; inspect "
                    "missing, modified, extra, or conflicting entries, and use "
                    f"`llm-wiki skills install --dest {report.dest_dir} --skill "
                    "wiki-reference --force` to restore expected regular files)"
                )
            other_skills = len(list_bundled_skills()) - 1
            if other_skills > 0:
                print(
                    f"{other_skills} more bundled workflow skills are available: "
                    "run `llm-wiki skills list`"
                )

    # 5. Persist the chosen agent so install-hook can read it
    config: dict[str, object] = {
        "agent": agent,
        "quality_hints": quality_hints,
        "reference_skill": install_skill,
        "issue_reporting": issue_reporting,
    }
    if source_selection is not None:
        config["source_selection"] = source_selection
    write_config(base_dir, config)

    print("LLM Wiki initialized successfully.")
