import os
from pathlib import Path

# Enhanced and consistent schema template for all agents
WIKI_INSTRUCTIONS = """
# --- LLM Wiki Maintainer Constraints ---
You are operating within an LLM Wiki architecture. The project's persistent memory is stored in `docs/llm_wiki/`.

## Before you start
- ALWAYS read `docs/llm_wiki/index.md` before planning a new feature or making architectural changes.
- Consult relevant entity and module pages to understand existing patterns before writing new code.

## When you change code
- UPDATE `docs/llm_wiki/entities/<ClassName>.md` when you add, modify, or remove a class.
- UPDATE `docs/llm_wiki/modules/<filename>.md` when you add, modify, or remove a module.
- UPDATE `docs/llm_wiki/workflows/<name>.md` when a cross-module flow changes.
- LOG a concise summary of your changes in `docs/llm_wiki/log.md` (append-only, newest at bottom).

## Quality checks
- Run `llm-wiki lint --wiki-dir docs/llm_wiki --src-dir .` to verify wiki consistency.
- Run `llm-wiki extract --src-dir .` to see the live AST inventory.
- Never leave the wiki in a state where lint reports errors.

## Formatting rules
- Entity pages must have: Location, Bases, Module link, Attributes table, Methods table, Relationships.
- Module pages must have: Path, Imports table, Classes summary, Functions table.
- Use relative markdown links between pages (e.g., `../entities/User.md`).
# --- End LLM Wiki Constraints ---
"""

# Agent-specific preambles prepended before the shared instructions
_CLAUDE_PREAMBLE = """\
# Project Wiki

This project uses an LLM Wiki for persistent architectural memory.
Read `docs/llm_wiki/index.md` first when starting any task.

"""

_CURSOR_PREAMBLE = """\
# Cursor Rules — LLM Wiki Project

This project maintains a living wiki at `docs/llm_wiki/`.
Always consult it before making changes.

"""

_COPILOT_PREAMBLE = """\
# Copilot Instructions — LLM Wiki Project

This project uses `docs/llm_wiki/` as persistent documentation.
Consult the wiki before suggesting changes.

"""

_GENERIC_PREAMBLE = """\
# Agent Instructions — LLM Wiki Project

This project uses `docs/llm_wiki/` for architectural memory.

"""

SCHEMA_TEMPLATES = {
    "claude": {"filename": "CLAUDE.md", "content": _CLAUDE_PREAMBLE + WIKI_INSTRUCTIONS},
    "cursor": {"filename": ".cursorrules", "content": _CURSOR_PREAMBLE + WIKI_INSTRUCTIONS},
    "copilot": {"filename": ".github/copilot-instructions.md", "content": _COPILOT_PREAMBLE + WIKI_INSTRUCTIONS},
    "aider": {"filename": ".aider.conf.yml", "content": _GENERIC_PREAMBLE + WIKI_INSTRUCTIONS},
    "opencode": {"filename": ".opencode/instructions.md", "content": _GENERIC_PREAMBLE + WIKI_INSTRUCTIONS},
    "generic": {"filename": ".agents.md", "content": _GENERIC_PREAMBLE + WIKI_INSTRUCTIONS},
}

def run(args):
    print(f"Initializing LLM Wiki with {args.agent} schema...")
    
    # 1. Create directory structure
    base_dir = Path("docs/llm_wiki")
    directories = [
        base_dir,
        base_dir / "entities",
        base_dir / "modules",
        base_dir / "workflows"
    ]
    
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)
        # Create empty .gitkeep so git tracks empty dirs
        (d / ".gitkeep").touch()
        
    print(f"Created wiki directories in {base_dir}/")
    
    # 2. Create core files if they don't exist
    index_path = base_dir / "index.md"
    if not index_path.exists():
        with open(index_path, "w") as f:
            f.write("# LLM Wiki Index\n\nCatalog of project modules and entities.\n\n## Entities\n\n## Modules\n\n## Workflows\n")
            
    log_path = base_dir / "log.md"
    if not log_path.exists():
        with open(log_path, "w") as f:
            f.write("# Architectural Log\n\nAppend-only chronological log.\n\n")

    # 3. Create or Append to Agent Schema
    schema = SCHEMA_TEMPLATES.get(args.agent)
    if schema:
        schema_path = Path(schema["filename"])
        # ensure parent exists (e.g. for .github/)
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        
        content_to_add = schema["content"]
        
        if schema_path.exists():
            with open(schema_path, "r") as f:
                existing_content = f.read()
                
            if "# --- LLM Wiki Maintainer Constraints ---" not in existing_content:
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
    
    print("LLM Wiki initialized successfully.")
