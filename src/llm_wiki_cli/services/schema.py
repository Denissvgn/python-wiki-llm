"""Shared schema utilities for agent constraint blocks.

Provides functions to build, strip, and replace the LLM Wiki constraint
block that is injected into agent schema files (CLAUDE.md, .cursorrules, etc.).
"""

from __future__ import annotations

import re
from pathlib import Path

from ..config import IDE_AGENTS

# Marker boundaries used to wrap the entire generated block
CONSTRAINT_START = "# --- LLM Wiki Maintainer Constraints ---"
CONSTRAINT_END = "# --- End LLM Wiki Constraints ---"

# Map from agent name to the schema file it uses
SCHEMA_FILENAMES: dict[str, str] = {
    "claude": "CLAUDE.md",
    "cursor": ".cursorrules",
    "copilot": ".github/copilot-instructions.md",
    "aider": ".aider.conf.yml",
    "opencode": ".opencode/instructions.md",
    "generic": ".agents.md",
}

# All possible schema files (superset — includes legacy names for uninstall)
ALL_SCHEMA_FILES: list[str] = [
    "CLAUDE.md",
    "AGENTS.md",
    ".cursorrules",
    ".github/copilot-instructions.md",
    ".agents.md",
    ".aider.conf.yml",
    ".opencode/instructions.md",
]

_IDE_SYNC_INSTRUCTIONS = """\

## How to sync the wiki in this IDE session
Because you run inside the IDE (not as a background CLI process), the wiki is NOT
updated automatically on commit. You are responsible for keeping it current:

1. **After every code change in this session** that adds, removes, or modifies a
   class, function, module, or cross-module flow:
   - Update the relevant `entities/` and `modules/` pages immediately.
   - If 3+ modules are now connected differently, update or create a `workflows/` page.
   - Append a one-line summary to `log.md`.
2. **To do a full re-sync manually**, run in the terminal:
   ```
   llm-wiki generate-prompt
   ```
   This builds a diff + AST prompt in `.git/llm-wiki-prompt.txt`. Open that file
   and paste its contents into this chat to trigger a full wiki update.
3. **Never skip the update** — a stale wiki defeats the purpose of the system.
"""


def _wiki_instructions(wiki_dir: str) -> str:
    return f"""You are operating within an LLM Wiki architecture. The project's persistent memory is stored in `{wiki_dir}/`.

## Before you start
- ALWAYS read `{wiki_dir}/index.md` before planning a new feature or making architectural changes.
- Consult relevant entity and module pages to understand existing patterns before writing new code.

## When you change code
- UPDATE `{wiki_dir}/entities/<ClassName>.md` when you add, modify, or remove a class.
- UPDATE `{wiki_dir}/modules/<filename>.md` when you add, modify, or remove a module.
- UPDATE `{wiki_dir}/workflows/<name>.md` when a cross-module flow changes.
- UPDATE `{wiki_dir}/infrastructure/<name>.md` when a Dockerfile or docker-compose file changes.
- LOG a concise summary of your changes in `{wiki_dir}/log.md` (append-only, newest at bottom).

## Quality checks
- Run `llm-wiki lint --wiki-dir {wiki_dir} --src-dir .` to verify wiki consistency.
- Run `llm-wiki extract --src-dir .` to see the live AST inventory.
- Never leave the wiki in a state where lint reports errors.

## Formatting rules
- Entity pages must have: Location, Bases, Module link, Attributes table, Methods table, Relationships.
- Module pages must have: Path, Imports table, Classes summary, Functions table.
- Infrastructure pages must have: Path, type-specific sections (stages, services, ports, env vars, etc.).
- Use relative markdown links between pages (e.g., `../entities/User.md`).
"""


def build_schema_content(agent: str, wiki_dir: str) -> str:
    """Build the full constraint block for the given agent and wiki directory."""
    instructions = _wiki_instructions(wiki_dir)
    preambles = {
        "claude": f"# Project Wiki\n\nThis project uses an LLM Wiki for persistent architectural memory.\nRead `{wiki_dir}/index.md` first when starting any task.\n\n",
        "cursor": f"# Cursor Rules — LLM Wiki Project\n\nThis project maintains a living wiki at `{wiki_dir}/`.\nAlways consult it before making changes.\n\n",
        "copilot": f"# Copilot Instructions — LLM Wiki Project\n\nThis project uses `{wiki_dir}/` as persistent documentation.\nConsult the wiki before suggesting changes.\n\n",
    }
    preamble = preambles.get(agent, f"# Agent Instructions — LLM Wiki Project\n\nThis project uses `{wiki_dir}/` for architectural memory.\n\n")
    extra = _IDE_SYNC_INSTRUCTIONS if agent in IDE_AGENTS else ""
    body = preamble + instructions + extra
    return f"{CONSTRAINT_START}\n{body.strip()}\n{CONSTRAINT_END}\n"


def strip_wiki_block(content: str) -> str:
    """Remove the LLM Wiki constraint block from file content.

    Handles the block including surrounding blank lines so the file
    stays clean after removal.
    """
    pattern = re.compile(
        r'\n*' + re.escape(CONSTRAINT_START) + r'.*?' + re.escape(CONSTRAINT_END) + r'\n*',
        re.DOTALL,
    )
    cleaned = pattern.sub('\n', content)
    return cleaned.strip() + '\n' if cleaned.strip() else ''


def replace_schema_block(schema_path: Path, new_content: str) -> None:
    """Replace the constraint block in an existing schema file, preserving user content.

    If the file has no existing block, the new content is appended.
    """
    if not schema_path.exists():
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path.write_text(new_content)
        return

    existing = schema_path.read_text()
    if CONSTRAINT_START not in existing:
        # No existing block — append
        sep = "\n\n" if existing and not existing.endswith("\n\n") else ("\n" if existing and not existing.endswith("\n") else "")
        schema_path.write_text(existing + sep + new_content)
        return

    # Replace existing block
    pattern = re.compile(
        re.escape(CONSTRAINT_START) + r'.*?' + re.escape(CONSTRAINT_END) + r'\n?',
        re.DOTALL,
    )
    updated = pattern.sub(new_content, existing)
    schema_path.write_text(updated)
