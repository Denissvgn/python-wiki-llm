from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from ..config import CLI_AGENTS, DEFAULT_WIKI_DIR, get_agent_config_path, validate_path
from ..services.schema import (
    CONSTRAINT_START as _CONSTRAINT_START,
    SCHEMA_FILENAMES,
    build_schema_content as _build_schema_content,
)


# Agents that have a real CLI executable (used by trigger-agent / install-hook)
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
            f"The schema file will be created, but background auto-sync\n"
            f"(`llm-wiki trigger-agent --agent {args.agent}`) will not work\n"
            f"until '{executable}' is installed.\n"
        )

    
    # 1. Create directory structure
    base_dir = Path(wiki_dir)
    directories = [
        base_dir,
        base_dir / "entities",
        base_dir / "modules",
        base_dir / "workflows",
        base_dir / "infrastructure",
    ]
    
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
        with open(index_path, "w") as f:
            f.write("# LLM Wiki Index\n\nCatalog of project modules and entities.\n\n## Entities\n\n## Modules\n\n## Workflows\n\n## Infrastructure\n")
            
    log_path = base_dir / "log.md"
    if not log_path.exists():
        with open(log_path, "w") as f:
            f.write("# Architectural Log\n\nAppend-only chronological log.\n\n")

    # 3. Create or Append to Agent Schema
    filename = SCHEMA_FILENAMES.get(args.agent)
    if filename:
        schema_path = Path(filename)
        # ensure parent exists (e.g. for .github/)
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        
        content_to_add = _build_schema_content(args.agent, wiki_dir)
        
        if schema_path.exists():
            with open(schema_path, "r") as f:
                existing_content = f.read()
                
            if _CONSTRAINT_START not in existing_content:
                with open(schema_path, "a") as f:
                    # Append cleanly
                    f.write("\n\n" + content_to_add)
                print(f"Appended agent constraints to existing file: {schema_path}")
            else:
                print(f"Agent constraints already exist in {schema_path}, skipping append.")
        else:
            with open(schema_path, "w") as f:
                f.write(content_to_add)
            print(f"Created agent schema file: {schema_path}")
    
    # 4. Persist the chosen agent so install-hook can read it
    agent_config_path = get_agent_config_path(base_dir)
    with open(agent_config_path, "w") as f:
        f.write(args.agent)

    # 5. Add llm-wiki temp files to .gitignore
    _GITIGNORE_ENTRIES = [
        ".git/llm-wiki-prompt.txt",
        ".git/llm-wiki.lock",
        ".git/llm-wiki-breaker.json",
        ".git/llm-wiki-sync.log",
    ]
    gitignore = Path(".gitignore")
    existing = gitignore.read_text() if gitignore.exists() else ""
    to_add = [e for e in _GITIGNORE_ENTRIES if e not in existing]
    if to_add:
        with open(gitignore, "a") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("# LLM Wiki temp files\n")
            for entry in to_add:
                f.write(entry + "\n")
        print(f"Added {len(to_add)} entries to .gitignore")

    print("LLM Wiki initialized successfully.")

