"""Shared schema utilities for agent constraint blocks.

Provides functions to build, strip, and replace the LLM Wiki constraint
block that is injected into agent schema files (CLAUDE.md, .cursorrules, etc.).
"""

from __future__ import annotations

import re
from pathlib import Path

from .io import read_md, write_md

# Marker boundaries used to wrap the entire generated block
CONSTRAINT_START = "# --- LLM Wiki Maintainer Constraints ---"
CONSTRAINT_END = "# --- End LLM Wiki Constraints ---"
SKILL_START_PREFIX = "# --- LLM Wiki Skill:"
SKILL_END_PREFIX = "# --- End LLM Wiki Skill:"

# Map from agent name to the schema file it uses
SCHEMA_FILENAMES: dict[str, str] = {
    "claude": "CLAUDE.md",
    "cursor": ".cursorrules",
    "copilot": ".github/copilot-instructions.md",
    "aider": ".aider.conf.yml",
    "opencode": ".opencode/instructions.md",
    "generic": "AGENTS.md",
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

_SYNC_INSTRUCTIONS = """\

## How to sync the wiki in this agent session
Generated hooks create a prompt file for human review instead of starting an
agent automatically on commit. You are responsible for keeping the wiki current:

1. **After every code change in this session** that adds, removes, or modifies a
   class, function, module, or cross-module flow:
   - Run `llm-wiki sync --jobs auto` from the project root.
   - If sync repairs only the manifest, run the same sync command again.
   - If sync stops on a large diff, inspect the changed files first. Re-run with
     `--force` only when the broad wiki update is intentional.
   - Inspect pages that sync created or updated. Replace generated placeholders,
     copied-docstring-only descriptions, and knowable `—` table descriptions
     with semantic notes from the diff and source.
   - If `dependencies.md` or `load-order.md` exists, inspect regenerated
     architecture pages too. Their `## Notes` sections are agent-owned: document
     intentional cycles, dynamic imports, side effects, and notable dependency
     rationale from the current change.
   - Run `llm-wiki lint --strict --jobs auto` to verify consistency. Fix any
     issues until it exits 0.
   - Treat Import cycles, undeclared dependencies, and unused dependencies as
     warning diagnostics that require review even when lint exits 0.
2. **When extractor helpers are missing** for TypeScript, Go, or Rust projects:
   ```
   llm-wiki prepare-extractors --src-dir .
   ```
   Then repeat the sync or lint command. Do not run npm/go/cargo helper setup
   manually; `prepare-extractors` owns that cache. If the Go executable on
   `PATH` cannot run, set `LLM_WIKI_GO=/path/to/go` and retry.
3. **To build a full update prompt manually**, run in the terminal:
   ```
   llm-wiki generate-prompt
   ```
   This builds a diff + AST prompt in `.git/llm-wiki-prompt.txt`. Open that file
   and paste its contents into this chat when a reviewed prompt is useful.
4. **Never skip the update** — a stale wiki defeats the purpose of the system.

## Using `llm-wiki sync` for incremental updates
`sync` compares source file hashes against a stored manifest and regenerates only
the wiki pages whose source has changed. Use it instead of a full re-bootstrap:

```
llm-wiki sync --jobs auto
```

- **When to use:** after pulling new code, after a rebase, or whenever you suspect
  the wiki is stale but don't want to regenerate everything.
- Sync creates/updates entity and module pages for new or changed files, marks
  removed files with a ⚠️ Stale header, and rebuilds `index.md`.
- When `dependencies.md` or `load-order.md` exists, sync also refreshes those
  dependency architecture pages and preserves their agent-owned `## Notes`
  sections by default. Projects bootstrapped with `--skip-dependencies`, or
  older wikis without those pages, stay untouched.
- Sync output is a deterministic AST/docstring skeleton. After it runs, agents
  must fill affected pages with project-specific semantics: responsibility,
  system role, collaborators, important behavior, and usage or constraints.
- Sync uses the same persistent inventory cache as lint when available. Use
  `--cache-stats` when you need to see cache behavior.
- If no manifest exists yet (project bootstrapped by an older version), sync will
  **seed a baseline manifest** from the current source state without modifying
  pages. Subsequent runs then work incrementally.
- If the stored manifest has invalid hashes, sync repairs the manifest without
  modifying pages. Re-run sync afterwards to apply source changes.
- Sync has a large-diff guard to prevent accidental mass rewrites. Use
  `llm-wiki sync --force` only after confirming the broad update is expected.
- After sync finishes, always run `llm-wiki lint --strict --jobs auto` to verify
  structure. Passing lint is not enough if affected pages still contain generic
  `_Auto-generated from ..._` text or unexplained placeholders.
- Lint reports Import cycles, undeclared dependencies, and unused dependencies
  as warning diagnostics for dependency architecture pages. Review and document
  intentional findings in the relevant `## Notes` section.

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
- First run `llm-wiki sync --jobs auto --wiki-dir {wiki_dir} --src-dir .` after
  code changes. Sync uses the manifest, persistent inventory cache, and
  collision-aware page naming to update only affected wiki pages.
- If sync reports that it repaired only the manifest, run the same sync command
  again before linting.
- If sync stops on a large diff, inspect the affected files. Use
  `llm-wiki sync --force --jobs auto --wiki-dir {wiki_dir} --src-dir .` only when
  the broad update is intentional.
- Then inspect the pages sync created or updated. Sync produces deterministic
  AST/docstring skeletons; you are responsible for the semantic pass.
- If `{wiki_dir}/dependencies.md` or `{wiki_dir}/load-order.md` exists, inspect
  those regenerated architecture pages too. Their `## Notes` sections are
  agent-owned: document intentional cycles, dynamic imports, side effects, and
  notable dependency rationale. Projects bootstrapped with
  `--skip-dependencies`, or older wikis without those pages, stay untouched.
- Enrich new or generic affected pages whose descriptions are `_Auto-generated
  from ..._`, copied docstrings only, or table cells with `—` where semantic
  context is knowable from the diff or source.
- Semantic content should explain responsibility, role in the system, main
  collaborators, important behavior, and usage or constraints.
- Keep semantic edits surgical: preserve generated structure, links, tables, and
  canonical filenames. Update only affected entity pages in
  `{wiki_dir}/entities/`, module pages in `{wiki_dir}/modules/`, workflow pages
  in `{wiki_dir}/workflows/`, user-flow pages in `{wiki_dir}/flows/`,
  infrastructure pages in `{wiki_dir}/infrastructure/`,
  and append one concise summary to `{wiki_dir}/log.md`.

## Wiki file naming rules
Page filenames **must** match the conventions enforced by `llm-wiki lint`:

- Treat `{wiki_dir}/index.md` as the source of truth for existing page names.
  Do not guess links from raw class names or filenames when collisions are
  possible. If in doubt, run `llm-wiki extract --src-dir .` and match the
  source path to the existing index entry.
- **Entity pages** (`entities/`): Use the class name as the file stem when it is
  unique (e.g., class `MyClass` → `MyClass.md`). When two classes in different
  modules share the same name, prefix with the disambiguated module page stem:
  `<module_page_stem>_<ClassName>.md` (e.g., `pkg_a_cli_Parser.md`).
- **Module pages** (`modules/`): Use the source path from the extractor,
  relative to `--src-dir`. A unique file stem uses `<stem>.md`
  (e.g., `cli.py` → `cli.md`, `main.rs` → `main.md`). When two files share the
  same stem in different directories, parent directory components are prepended
  with underscores until unique (e.g., `pkg_a/cli.py` and `pkg_b/cli.py` →
  `pkg_a_cli.md` and `pkg_b_cli.md`).
- **Infrastructure pages** (`infrastructure/`): Take the relative path of the
  Docker/Compose file and replace `/` and `.` with `_`
  (e.g., `Dockerfile` → `Dockerfile.md`, `test_project/Dockerfile` →
  `test_project_Dockerfile.md`, `docker-compose.yml` → `docker-compose_yml.md`).
  Links from infrastructure pages to source modules must target the actual
  module page stem from `index.md`; if a COPY/ADD source is ambiguous, leave it
  as code text instead of creating a guessed link.
- **Workflow pages** (`workflows/`): Free-form descriptive names.
- **User-flow pages** (`flows/`): Named by entry-point id (`<category>-<symbol>`,
  e.g. `api-extract_source.md`, `process-llm-wiki.md`). Do not rename them.

## Quality checks
- Your wiki changes are **structurally valid** when `llm-wiki lint --strict --jobs auto --wiki-dir {wiki_dir} --src-dir .` exits 0.
- Lint passing is not enough: affected pages must also have semantic
  explanations, not only generated skeletons or copied docstrings.
- Run lint after every wiki update. If it reports issues, fix them and re-run until it passes.
- Run `llm-wiki lint --profile --cache-stats --wiki-dir {wiki_dir} --src-dir .`
  when lint is slow or extractor failures need machine-readable diagnostics.
- Treat Import cycles, undeclared dependencies, and unused dependencies as
  warning diagnostics that require review even when lint exits 0.
- Run `llm-wiki extract --src-dir .` to see the live AST inventory when you need detail.
- If TypeScript, Go, or Rust extraction reports a missing prepared helper, run
  `llm-wiki prepare-extractors --src-dir .` once and repeat the failed command.
- If Go is installed but not runnable through `PATH`, set
  `LLM_WIKI_GO=/path/to/go` before preparing extractors.
- Never leave the wiki in a state where lint reports errors.

## Formatting rules
- Entity pages must have: Location, Bases, Module link, Attributes table, Methods table, Relationships.
- Module pages must have: Path, Imports table, Classes summary, Functions table.
- User-flow pages have a generated Mermaid call-sequence diagram; fill in the
  `## Behavior` section with what the flow does, its triggers, and side effects.
  Do not edit the generated diagram by hand.
- Infrastructure pages must have: Path, type-specific sections (stages, services, ports, env vars, etc.).
- Dependency architecture pages must keep any human-authored `## Notes` section
  aligned with current cycles, external dependency reconciliation, load-order
  caveats, and dynamic behavior that static extraction cannot prove.
- Use relative markdown links between pages (e.g., `../entities/User.md`).
"""


def build_schema_content(
    agent: str, wiki_dir: str, *, quality_hints: bool = True
) -> str:
    """Build the full constraint block for the given agent and wiki directory."""
    instructions = _wiki_instructions(wiki_dir)
    preambles = {
        "claude": f"# Project Wiki\n\nThis project uses an LLM Wiki for persistent architectural memory.\nRead `{wiki_dir}/index.md` first when starting any task.\n\n",
        "cursor": f"# Cursor Rules — LLM Wiki Project\n\nThis project maintains a living wiki at `{wiki_dir}/`.\nAlways consult it before making changes.\n\n",
        "copilot": f"# Copilot Instructions — LLM Wiki Project\n\nThis project uses `{wiki_dir}/` as persistent documentation.\nConsult the wiki before suggesting changes.\n\n",
    }
    preamble = preambles.get(
        agent,
        f"# Agent Instructions — LLM Wiki Project\n\nThis project uses `{wiki_dir}/` for architectural memory.\n\n",
    )
    hints = _QUALITY_HINTS if quality_hints else ""
    extra = _SYNC_INSTRUCTIONS
    body = preamble + instructions + hints + extra
    return f"{CONSTRAINT_START}\n{body.strip()}\n{CONSTRAINT_END}\n"


def strip_wiki_block(content: str) -> str:
    """Remove the LLM Wiki constraint block from file content.

    Handles the block including surrounding blank lines so the file
    stays clean after removal.
    """
    pattern = re.compile(
        r"\n*"
        + re.escape(CONSTRAINT_START)
        + r".*?"
        + re.escape(CONSTRAINT_END)
        + r"\n*",
        re.DOTALL,
    )
    cleaned = pattern.sub("\n", content)
    return cleaned.strip() + "\n" if cleaned.strip() else ""


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
        sep = (
            "\n\n"
            if existing and not existing.endswith("\n\n")
            else ("\n" if existing and not existing.endswith("\n") else "")
        )
        write_md(schema_path, existing + sep + new_content)
        return

    # Replace existing block (consume any trailing whitespace after CONSTRAINT_END
    # so repeated runs don't accumulate blank lines)
    pattern = re.compile(
        re.escape(CONSTRAINT_START) + r".*?" + re.escape(CONSTRAINT_END) + r"\n*",
        re.DOTALL,
    )
    updated = pattern.sub(lambda _m: new_content, existing)
    write_md(schema_path, updated)


def skill_start_marker(plugin_id: str, skill_id: str) -> str:
    return f"{SKILL_START_PREFIX} {plugin_id}/{skill_id} ---"


def skill_end_marker(plugin_id: str, skill_id: str) -> str:
    return f"{SKILL_END_PREFIX} {plugin_id}/{skill_id} ---"


def build_skill_block(plugin_id: str, skill_id: str, skill_content: str) -> str:
    body = skill_content.strip()
    return f"{skill_start_marker(plugin_id, skill_id)}\n{body}\n{skill_end_marker(plugin_id, skill_id)}\n"


def strip_skill_blocks(
    content: str, *, plugin_id: str | None = None, skill_id: str | None = None
) -> str:
    """Remove managed plugin skill blocks from schema content."""
    if plugin_id and skill_id:
        start = re.escape(skill_start_marker(plugin_id, skill_id))
        end = re.escape(skill_end_marker(plugin_id, skill_id))
        pattern = re.compile(r"\n*" + start + r".*?" + end + r"\n*", re.DOTALL)
    elif plugin_id:
        pattern = re.compile(
            r"\n*"
            + re.escape(SKILL_START_PREFIX)
            + r"\s+"
            + re.escape(plugin_id)
            + r"/[A-Za-z0-9_.-]+\s+---.*?"
            + re.escape(SKILL_END_PREFIX)
            + r"\s+"
            + re.escape(plugin_id)
            + r"/[A-Za-z0-9_.-]+\s+---\n*",
            re.DOTALL,
        )
    else:
        pattern = re.compile(
            r"\n*"
            + re.escape(SKILL_START_PREFIX)
            + r"\s+[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\s+---.*?"
            + re.escape(SKILL_END_PREFIX)
            + r"\s+[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\s+---\n*",
            re.DOTALL,
        )
    cleaned = pattern.sub("\n", content)
    return cleaned.strip() + "\n" if cleaned.strip() else ""


def replace_skill_block(
    schema_path: Path, plugin_id: str, skill_id: str, skill_content: str
) -> None:
    new_content = build_skill_block(plugin_id, skill_id, skill_content)
    if not schema_path.exists():
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        write_md(schema_path, new_content)
        return

    existing = read_md(schema_path).replace("\r\n", "\n").replace("\r", "\n")
    existing = strip_skill_blocks(existing, plugin_id=plugin_id, skill_id=skill_id)
    sep = (
        "\n\n"
        if existing and not existing.endswith("\n\n")
        else ("\n" if existing and not existing.endswith("\n") else "")
    )
    write_md(schema_path, existing + sep + new_content)


def refresh_skill_blocks(agent: str, wiki_dir: str) -> list[str]:
    """Refresh all installed skill blocks in the active agent schema file."""
    from .plugins import iter_components, read_component_text

    filename = SCHEMA_FILENAMES.get(agent)
    if not filename:
        return []

    schema_path = Path(filename)
    refreshed: list[str] = []
    for component in iter_components("skill"):
        plugin_id = component["plugin_id"]
        skill_id = component["id"]
        replace_skill_block(
            schema_path, plugin_id, skill_id, read_component_text(component)
        )
        refreshed.append(f"{plugin_id}/{skill_id}")
    return refreshed


def strip_plugin_skill_blocks(plugin_id: str) -> list[str]:
    """Strip one plugin's skill blocks from every known schema file."""
    touched: list[str] = []
    for filename in ALL_SCHEMA_FILES:
        path = Path(filename)
        if not path.exists():
            continue
        existing = read_md(path)
        updated = strip_skill_blocks(existing, plugin_id=plugin_id)
        if updated != existing:
            write_md(path, updated)
            touched.append(filename)
    return touched
