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
   class, function, module, or cross-module flow, run the full sync-then-lint
   workflow from "When you change code" above, including the semantic pass on
   affected pages and the dependency/flow page reviews it describes. The
   bundled `wiki-sync` skill documents the full operational loop (change
   classification, semantic-only edit guardrails, failure modes).
2. **When extractor helpers are missing** for TypeScript/JavaScript, Go, Rust, or Haskell projects:
   ```
   llm-wiki prepare-extractors --src-dir .
   ```
   Then repeat the sync or lint command. Do not run npm/go/cargo/ghc helper setup
   manually; `prepare-extractors` owns that cache. Toolchain fallbacks and
   cache separation are documented in the `wiki-reference` skill's "Extractor
   helpers and toolchains" section.
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
- Sync output is a deterministic AST/docstring skeleton. After it runs, agents
  must fill affected pages with project-specific semantics as described in
  "When you change code".
- Sync uses the same persistent inventory cache as lint when available. Use
  `--cache-stats` when you need to see cache behavior.
- If no manifest exists yet (project bootstrapped by an older version), sync will
  **seed a baseline manifest** from the current source state without modifying
  pages. Subsequent runs then work incrementally.
- Sync has a large-diff guard to prevent accidental mass rewrites. Use
  `llm-wiki sync --force` only after confirming the broad update is expected.
- After sync finishes, always run `llm-wiki lint --strict --jobs auto` and apply
  the review rules under "Quality checks". Passing lint is not enough if
  affected pages still contain generic `_Auto-generated from ..._` text or
  unexplained placeholders.

## Large codebases
Before a complex task on a large project, run
`llm-wiki context --budget <TOKENS> --src-dir . --format markdown --focus changed`
for a token-budgeted, priority-ranked snapshot of the codebase. Flag semantics
are documented in the `wiki-reference` skill.
"""

_QUALITY_HINTS = """\

## Agent quality guidelines
- **Surgical Changes:** Only modify wiki pages directly affected by your code change.
  Don't "improve" adjacent pages, reformat existing content, or refactor unrelated docs.
- **Think Before Editing:** If a wiki page structure is unclear, state what's confusing
  rather than guessing. Don't silently rewrite pages you don't fully understand.
"""


def _issue_reporting_instructions(wiki_dir: str) -> str:
    return f"""## Report llm-wiki tool issues
If an `llm-wiki` command itself misbehaves while you use it — a crash or
traceback, wrong or stale generated output, a diagnostic that contradicts the
observed state, or behavior that contradicts these instructions — never work
around it silently:

- Write one report file per issue under `llm-wiki-issues/` at the project root,
  named `llm-wiki-issues/<YYYY-MM-DD>-<short-slug>.md`. Keep reports outside
  `{wiki_dir}/` so lint does not flag them as orphan pages.
- Each report must include: the exact command and flags you ran, expected
  behavior, actual behavior (trim long output to the relevant lines), minimal
  reproduction steps, `llm-wiki --version` output, and the workaround you
  applied, if any.
- Then continue the original task with the safest workaround and mention the
  report file in your final summary so the issue can be addressed upstream.

"""


def _wiki_instructions(
    wiki_dir: str, skills_dir: str, *, issue_reporting: bool = False
) -> str:
    issue_reporting_instructions = (
        _issue_reporting_instructions(wiki_dir) if issue_reporting else ""
    )
    return f"""You are operating within an LLM Wiki architecture. The project's persistent memory is stored in `{wiki_dir}/`.

## Before you start
- ALWAYS read `{wiki_dir}/index.md` before planning a new feature or making architectural changes.
- Consult relevant entity and module pages to understand existing patterns before writing new code.

## Deep reference (read on demand)
Contract-level detail lives in the bundled `wiki-reference` skill at
`{skills_dir}/wiki-reference/reference.md` (restore it with
`llm-wiki skills install`, or `llm-wiki skills export --dest exported-skills`
for any other location). Read the matching section before
interpreting extractor, dependency, or site-check diagnostics — it covers
extraction contracts (including Haskell), helper toolchains and caches,
dependency reconciliation and lockfile `versions` metadata, static-site
export profiles, and `llm-wiki context`. Do not read it upfront.

## Canonical wiki surfaces
The canonical wiki surfaces are:

- `{wiki_dir}/index.md`: mixed generated table of contents and navigational context.
- `{wiki_dir}/log.md`: generated or agent-appended architectural change log.
- `{wiki_dir}/entities/`: semantic entity pages with generated structure and
  generated `## Relationships` diagrams/tables when relationship metadata
  exists.
- `{wiki_dir}/modules/`: semantic source-module pages with generated structure
  and generated `## Local dependency map` sections when dependency analysis is
  enabled.
- `{wiki_dir}/workflows/`: mixed cross-module workflow pages.
- `{wiki_dir}/guides/`: semantic agent-authored onboarding, operator, and
  contributor guides. `sync` does not generate or overwrite guide prose.
- `{wiki_dir}/flows/`: mixed user-flow pages generated from entry points.
- `{wiki_dir}/infrastructure/`: mixed Docker, Compose, GitHub Actions,
  Kubernetes, and targeted runtime/config YAML pages.
- `{wiki_dir}/api-contracts.md`: optional mixed production HTTP contract
  inventory generated from static FastAPI analysis or an exported OpenAPI file;
  its `## Notes` section is semantic.
- `{wiki_dir}/dependencies.md`: mixed dependency architecture page when present.
- `{wiki_dir}/load-order.md`: mixed load-order architecture page when present.
- `{wiki_dir}/.llm-wiki-surface.json`: generated machine-readable surface index
  with page metadata, source mappings, flow metadata, dependency-page presence,
  counts, and outgoing internal links.

Static-site mirror output, when present, is derived from these canonical
surfaces. Treat it as generated distribution output built and validated with
`llm-wiki site export|check`, not as an editable source of truth. Export
profiles, MkDocs/Docusaurus specifics, and site checker modes are documented
in the `wiki-reference` skill's "Static-site export" section.

## User docs and usage examples
Use the bundled docs workflow skills in this order when the goal is a
human-facing documentation layer with captured examples:

`wiki-bootstrap -> wiki-sync -> user-docs-author -> usage-examples -> publish-docs`

External autonomous agents can consume the same instructions without a
dedicated agent registration:

```bash
llm-wiki init --agent generic --wiki-dir {wiki_dir}
llm-wiki skills export --dest exported-skills
```

Hard rules for every agent:

- Edit semantic prose only; generated blocks are CLI-owned.
- Keep source targets read-only unless the user explicitly asks for source edits.
- Do not run toolchain installs for capture; no toolchain installs are part of
  this workflow. Capture tooling comes from the agent platform, and missing
  capture tooling becomes a deferred item.
- Place usage media under `assets/<surface>/<page-stem>/`.
- Run the validation loop before commit: lint, site export, site check, and
  built-site checks when a builder exists.
- Keep wiki commits separate from code commits.
- Captures must demonstrate behavior already backed by wiki/source evidence.

Do not edit generated Mermaid diagrams by hand. Treat generated diagrams,
tables, links, headings, canonical filenames, and machine-readable artifacts as
CLI-owned structure. Keep semantic sections such as descriptions, `## Behavior`,
`## Notes`, and log summaries aligned with the current source.
Diagram style plugins may configure generated Mermaid flowchart direction,
node classes, and class colors, but they cannot inject arbitrary Markdown,
labels, hrefs, or raw Mermaid content.

## When you change code
- First run `llm-wiki sync --jobs auto --wiki-dir {wiki_dir} --src-dir .` after
  code changes. Sync uses the manifest, persistent inventory cache, and
  collision-aware page naming to update only affected wiki pages.
- If this wiki was bootstrapped from a trusted source root outside the current
  working directory, pass the same external `--src-dir` with
  `--allow-external-src` to `sync`, `lint`, and `ci-check`; `--wiki-dir` still
  uses the project-root write guard.
- If sync repairs only the manifest (its stored hashes were invalid, and no
  pages were modified), run the same sync command again before linting.
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
- If `{wiki_dir}/api-contracts.md` exists, inspect its declared operations,
  static-analysis unknowns, OpenAPI reconciliation diagnostics, and preserved
  `## Notes`; never treat an unknown contract field as a confirmed value.
- If `{wiki_dir}/flows/` exists, inspect regenerated user-flow pages too. Treat
  generated `## Data flow` sections, boundary effects, and static-analysis gaps
  as review inputs, then keep the human-authored `## Behavior` section aligned
  with observed side effects and outputs.
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
  `<module_page_stem>_<ClassName>.md` (e.g., `pkg_a_cli_Parser.md`). When the
  same class name appears more than once in one source file, suffix later
  occurrences with their one-based occurrence number (e.g., `Parser.md`,
  `Parser_2.md`).
- **Module pages** (`modules/`): Use the source path from the extractor,
  relative to `--src-dir`. A unique file stem uses `<stem>.md`
  (e.g., `cli.py` → `cli.md`, `main.rs` → `main.md`). When two files share the
  same stem in different directories, parent directory components are prepended
  with underscores until unique (e.g., `pkg_a/cli.py` and `pkg_b/cli.py` →
  `pkg_a_cli.md` and `pkg_b_cli.md`). If that still collides with another page
  id, all members of that collision use deterministic source-path context
  (e.g., `scripts_compliance_report.md`).
- **Infrastructure pages** (`infrastructure/`): Take the relative path of the
  Docker/Compose, GitHub Actions, Kubernetes, or targeted runtime/config YAML
  file and replace `/` and `.` with `_`
  (e.g., `Dockerfile` → `Dockerfile.md`, `test_project/Dockerfile` →
  `test_project_Dockerfile.md`, `docker-compose.yml` → `docker-compose_yml.md`,
  `.github/workflows/ci.yml` → `_github_workflows_ci_yml.md`).
  Links from infrastructure pages to source modules must target the actual
  module page stem from `index.md`; if a COPY/ADD source is ambiguous, leave it
  as code text instead of creating a guessed link.
- **Workflow pages** (`workflows/`): Free-form descriptive names.
- **Guide pages** (`guides/`): Free-form descriptive names for agent-owned
  onboarding, operator, or contributor narratives. Keep guide pages linked from
  `index.md` or another canonical page so they are discoverable and lint-clean.
- **User-flow pages** (`flows/`): Named by entry-point id (`<category>-<symbol>`,
  e.g. `api-extract_source.md`, `process-llm-wiki.md`). Do not rename them.

## Quality checks
- Your wiki changes are **structurally valid** when `llm-wiki lint --strict --jobs auto --wiki-dir {wiki_dir} --src-dir .` exits 0.
- For a trusted source root outside the current working directory, run
  `llm-wiki lint --strict --jobs auto --wiki-dir {wiki_dir} --src-dir <repo> --allow-external-src`;
  `--wiki-dir` still uses the project-root write guard.
- Lint passing is not enough: affected pages must also have semantic
  explanations, not only generated skeletons or copied docstrings.
- Run lint after every wiki update. If it reports issues, fix them and re-run until it passes.
- Run `llm-wiki lint --profile --cache-stats --wiki-dir {wiki_dir} --src-dir .`
  when lint is slow or extractor failures need machine-readable diagnostics.
- Treat Import cycles, undeclared dependencies, and unused dependencies as
  warning diagnostics that require review even when lint exits 0. Before
  acting on one, read the `wiki-reference` skill's "Dependency reconciliation"
  section — manifest scoping, import aliases, Go `// indirect`, and lockfile
  `versions` metadata rules live there.
- Run `llm-wiki extract --src-dir .` to see the live AST inventory when you need detail.
- If TypeScript/JavaScript, Go, Rust, or Haskell extraction reports a missing prepared helper, run
  `llm-wiki prepare-extractors --src-dir .` once and repeat the failed command.
  Toolchain fallbacks (`LLM_WIKI_GO`, `LLM_WIKI_GHC`), helper/inventory cache
  separation, Go test-file inclusion, and per-language extraction contracts
  (including the Haskell helper and inventory schema) are documented in the
  `wiki-reference` skill.
- If lint or CI reports unsupported sources, do not claim those files were
  documented. Either install a matching extractor plugin or note that the wiki
  covers active extractor languages only.
- Never leave the wiki in a state where lint reports errors.

{issue_reporting_instructions}## Formatting rules
- Entity pages must have: Location, Bases, Module link, Attributes table, Methods table, Relationships.
- Module pages must have: Path, Imports table, Classes summary, Functions table.
- User-flow pages have generated Mermaid call-sequence and `## Data flow`
  diagrams. Review static-analysis gaps and boundary effects, then fill in the
  `## Behavior` section with what the flow does, its triggers, observed side
  effects, and outputs. Do not edit generated diagrams by hand.
- Infrastructure pages must have: Path, type-specific sections (stages, services, ports, env vars, etc.).
- Dependency architecture pages must keep any human-authored `## Notes` section
  aligned with current cycles, external dependency reconciliation, load-order
  caveats, and dynamic behavior that static extraction cannot prove.
- Use relative markdown links between pages (e.g., `../entities/User.md`).
"""


def build_schema_content(
    agent: str,
    wiki_dir: str,
    *,
    quality_hints: bool = True,
    issue_reporting: bool = False,
) -> str:
    """Build the full constraint block for the given agent and wiki directory."""
    from .skills import skills_install_dir

    instructions = _wiki_instructions(
        wiki_dir,
        skills_install_dir(agent).as_posix(),
        issue_reporting=issue_reporting,
    )
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
