from __future__ import annotations

import shutil
import sys
from pathlib import Path

from ..config import CLI_AGENTS, DEFAULT_WIKI_DIR, validate_path, write_config
from ..services.io import read_md, write_md
from ..services.schema import (
    CONSTRAINT_START as _CONSTRAINT_START,
    SCHEMA_FILENAMES,
    build_schema_content as _build_schema_content,
)
from ..services.skills import (
    REFERENCE_SKILL_ID,
    SkillsError,
    install_reference_skill,
    list_bundled_skills,
)
from ..services.wiki_surface import iter_directory_kinds


# Agents that have a real CLI executable for explicit trigger-agent use.
_CLI_AGENTS = CLI_AGENTS


def run(args):
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(wiki_dir, "--wiki-dir")
    print(f"Initializing LLM Wiki with {args.agent} schema...")

    # Warn if the agent has a CLI executable that isn't installed
    executable = _CLI_AGENTS.get(args.agent)
    if executable and not shutil.which(executable):
        print(
            f"\nWarning: '{executable}' is not installed or not on PATH.\n"
            f"The schema file will be created, but manual agent execution\n"
            f"(`llm-wiki trigger-agent --agent {args.agent}`) will not work\n"
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
        write_md(
            index_path,
            "# LLM Wiki Index\n\nCatalog of project modules and entities.\n\n## Entities\n\n## Modules\n\n## Workflows\n\n## Guides\n\n## Infrastructure\n",
        )

    log_path = base_dir / "log.md"
    if not log_path.exists():
        write_md(log_path, "# Architectural Log\n\nAppend-only chronological log.\n\n")

    # 3. Create or Append to Agent Schema
    quality_hints = not getattr(args, "no_quality_hints", False)
    filename = SCHEMA_FILENAMES.get(args.agent)
    if filename:
        schema_path = Path(filename)
        # ensure parent exists (e.g. for .github/)
        schema_path.parent.mkdir(parents=True, exist_ok=True)

        content_to_add = _build_schema_content(
            args.agent, wiki_dir, quality_hints=quality_hints
        )

        if schema_path.exists():
            existing_content = read_md(schema_path)

            if _CONSTRAINT_START not in existing_content:
                write_md(schema_path, existing_content + "\n\n" + content_to_add)
                print(f"Appended agent constraints to existing file: {schema_path}")
            else:
                print(
                    f"Agent constraints already exist in {schema_path}, skipping append."
                )
        else:
            write_md(schema_path, content_to_add)
            print(f"Created agent schema file: {schema_path}")

    # 4. Install the CLI-owned wiki-reference skill that the constraint
    # block's deep-reference pointers target
    install_skill = not getattr(args, "no_skills", False)
    if install_skill:
        try:
            report = install_reference_skill(agent=args.agent)
        except SkillsError as exc:
            print(f"Warning: could not install {REFERENCE_SKILL_ID} skill: {exc}")
        else:
            if report.ok:
                print(f"Installed {REFERENCE_SKILL_ID} skill in {report.dest_dir}/")
            else:
                print(
                    f"Kept existing {REFERENCE_SKILL_ID} skill files in "
                    f"{report.dest_dir}/ (differ from bundled; run "
                    "`llm-wiki upgrade` or `llm-wiki skills install --force` "
                    "to refresh)"
                )
            other_skills = len(list_bundled_skills()) - 1
            if other_skills > 0:
                print(
                    f"{other_skills} more bundled workflow skills are available: "
                    "run `llm-wiki skills list`"
                )

    # 5. Persist the chosen agent so install-hook can read it
    write_config(
        base_dir,
        {
            "agent": args.agent,
            "quality_hints": quality_hints,
            "reference_skill": install_skill,
        },
    )

    print("LLM Wiki initialized successfully.")
