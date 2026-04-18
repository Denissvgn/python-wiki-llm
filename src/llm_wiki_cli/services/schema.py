"""Shared schema utilities for agent constraint blocks.

Provides functions to build, strip, and replace the LLM Wiki constraint
block that is injected into agent schema files (CLAUDE.md, .cursorrules, etc.).
"""

from __future__ import annotations

import re
from pathlib import Path

from ..config import IDE_AGENTS
from .io import read_md, write_md

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
   - Update the affected `entities/`, `modules/`, `workflows/`, and `infrastructure/` pages.
   - Append a one-line summary to `log.md`.
   - Run `llm-wiki lint` to verify your changes. Fix any issues until it exits 0.
2. **To do a full re-sync manually**, run in the terminal:
   ```
   llm-wiki generate-prompt
   ```
   This builds a diff + AST prompt in `.git/llm-wiki-prompt.txt`. Open that file
   and paste its contents into this chat to trigger a full wiki update.
3. **Never skip the update** — a stale wiki defeats the purpose of the system.

## Using `llm-wiki sync` for incremental updates
`sync` compares source file hashes against a stored manifest and regenerates only
the wiki pages whose source has changed. Use it instead of a full re-bootstrap:

```
llm-wiki sync
```

- **When to use:** after pulling new code, after a rebase, or whenever you suspect
  the wiki is stale but don't want to regenerate everything.
- Sync creates/updates entity and module pages for new or changed files, marks
  removed files with a ⚠️ Stale header, and rebuilds `index.md`.
- If no manifest exists yet (project bootstrapped by an older version), sync will
  **seed a baseline manifest** from the current source state without modifying
  pages. Subsequent runs then work incrementally.
- After sync finishes, always run `llm-wiki lint` to verify consistency.

## Using `llm-wiki context` for large codebases
`context` produces a token-budgeted, priority-ranked snapshot of the codebase —
ideal for feeding into an LLM prompt when the full extract output is too large:

```
llm-wiki context --budget <TOKENS> --src-dir . --format markdown --focus changed
```

- **`--budget`** (required): maximum token count for the output.
- **`--focus changed`** (default): prioritises files from the last git commit.
  Changed files get full detail, their 1-hop import neighbours get slim detail,
  everything else gets names only. Use `--focus all` to treat every file equally.
- **`--format`**: `json` (default, structured) or `markdown` (human-readable with
  tier-labelled sections).
- **When to use:** before starting a complex task on a large project, pass the
  context output to the agent so it has an accurate, right-sized view of the
  codebase without exceeding the context window.
"""

_QUALITY_HINTS = """\

## Agent quality guidelines
- **Surgical Changes:** Only modify wiki pages directly affected by your code change.
  Don't "improve" adjacent pages, reformat existing content, or refactor unrelated docs.
- **Think Before Editing:** If a wiki page structure is unclear, state what's confusing
  rather than guessing. Don't silently rewrite pages you don't fully understand.
"""


def _wiki_instructions(wiki_dir: str) -> str:
    return f"""You are operating within an LLM Wiki architecture. The project's persistent memory is stored in `{wiki_dir}/`.

## Before you start
- ALWAYS read `{wiki_dir}/index.md` before planning a new feature or making architectural changes.
- Consult relevant entity and module pages to understand existing patterns before writing new code.

## When you change code
- UPDATE entity pages in `{wiki_dir}/entities/` when you add, modify, or remove a class.
- UPDATE module pages in `{wiki_dir}/modules/` when you add, modify, or remove a module.
- UPDATE `{wiki_dir}/workflows/<name>.md` when a cross-module flow changes.
- UPDATE infrastructure pages in `{wiki_dir}/infrastructure/` when a Dockerfile or docker-compose file changes.
- LOG a concise summary of your changes in `{wiki_dir}/log.md` (append-only, newest at bottom).

## Wiki file naming rules
Page filenames **must** match the conventions enforced by `llm-wiki lint`:

- **Entity pages** (`entities/`): Use the class name as the file stem
  (e.g., class `MyClass` → `MyClass.md`). When two classes in different modules
  share the same name, prefix with the disambiguated module stem:
  `<module_stem>_<ClassName>.md` (e.g., `pkg_a_cli_Parser.md`).
- **Module pages** (`modules/`): Use the source file stem — the filename without
  its extension (e.g., `cli.py` → `cli.md`, `main.rs` → `main.md`). When two
  files share the same stem in different directories, parent directory components
  are prepended with underscores until unique (e.g., `pkg_a/cli.py` and
  `pkg_b/cli.py` → `pkg_a_cli.md` and `pkg_b_cli.md`).
- **Infrastructure pages** (`infrastructure/`): Take the relative path of the
  Docker/Compose file and replace `/` and `.` with `_`
  (e.g., `Dockerfile` → `Dockerfile.md`, `test_project/Dockerfile` →
  `test_project_Dockerfile.md`, `docker-compose.yml` → `docker-compose_yml.md`).
- **Workflow pages** (`workflows/`): Free-form descriptive names.

## Quality checks
- Your wiki changes are **complete** when `llm-wiki lint --wiki-dir {wiki_dir} --src-dir .` exits 0.
- Run lint after every wiki update. If it reports issues, fix them and re-run until it passes.
- Run `llm-wiki extract --src-dir .` to see the live AST inventory when you need detail.
- Never leave the wiki in a state where lint reports errors.

## Formatting rules
- Entity pages must have: Location, Bases, Module link, Attributes table, Methods table, Relationships.
- Module pages must have: Path, Imports table, Classes summary, Functions table.
- Infrastructure pages must have: Path, type-specific sections (stages, services, ports, env vars, etc.).
- Use relative markdown links between pages (e.g., `../entities/User.md`).
"""


def build_schema_content(agent: str, wiki_dir: str, *, quality_hints: bool = True) -> str:
    """Build the full constraint block for the given agent and wiki directory."""
    instructions = _wiki_instructions(wiki_dir)
    preambles = {
        "claude": f"# Project Wiki\n\nThis project uses an LLM Wiki for persistent architectural memory.\nRead `{wiki_dir}/index.md` first when starting any task.\n\n",
        "cursor": f"# Cursor Rules — LLM Wiki Project\n\nThis project maintains a living wiki at `{wiki_dir}/`.\nAlways consult it before making changes.\n\n",
        "copilot": f"# Copilot Instructions — LLM Wiki Project\n\nThis project uses `{wiki_dir}/` as persistent documentation.\nConsult the wiki before suggesting changes.\n\n",
    }
    preamble = preambles.get(agent, f"# Agent Instructions — LLM Wiki Project\n\nThis project uses `{wiki_dir}/` for architectural memory.\n\n")
    hints = _QUALITY_HINTS if quality_hints else ""
    extra = _IDE_SYNC_INSTRUCTIONS if agent in IDE_AGENTS else ""
    body = preamble + instructions + hints + extra
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
        write_md(schema_path, new_content)
        return

    existing = read_md(schema_path)
    # Normalize newlines for consistent matching
    existing = existing.replace("\r\n", "\n").replace("\r", "\n")
    if CONSTRAINT_START not in existing:
        # No existing block — append
        sep = "\n\n" if existing and not existing.endswith("\n\n") else ("\n" if existing and not existing.endswith("\n") else "")
        write_md(schema_path, existing + sep + new_content)
        return

    # Replace existing block (consume any trailing whitespace after CONSTRAINT_END
    # so repeated runs don't accumulate blank lines)
    pattern = re.compile(
        re.escape(CONSTRAINT_START) + r'.*?' + re.escape(CONSTRAINT_END) + r'\n*',
        re.DOTALL,
    )
    updated = pattern.sub(new_content, existing)
    write_md(schema_path, updated)
