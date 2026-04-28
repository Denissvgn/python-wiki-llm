# LLM Wiki CLI

## About

LLM Wiki CLI helps coding agents keep project documentation accurate automatically. It builds and maintains a structured wiki from your source code, validates consistency with lint checks, and supports automated or prompt-driven sync workflows after each commit.

It is designed for teams using AI-assisted development who want less context drift, better architectural memory, and a repo-level documentation process that scales across Python, TypeScript, Go, Rust, and Docker/Compose infrastructure.

A companion CLI designed to help Native LLM Coding Agents (like Claude Code, OpenCode, Cursor, Copilot, or Aider) autonomously maintain a persistent architectural memory ("Wiki") of your projects.

By providing constant, up-to-date documentation via a local wiki, your LLM agents will stop rediscovering project boundaries from scratch upon every interaction. Instead, the agent learns to consult the `docs/llm_wiki` first, and updates it gracefully whenever a commit alters the software architecture.

Supports **Python, TypeScript, Go, and Rust** projects. Infrastructure documentation (Docker/Compose) included.

> Inspired by Andrej Karpathy's post on [LLM-native development workflows](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

> **Warning:** This tool grants **full unsupervised permissions** to background agents (e.g. `--dangerously-skip-permissions` for Claude Code). The post-commit hook runs headlessly with no human-in-the-loop confirmation. Use with caution — review your agent's capabilities and ensure you trust the execution environment before enabling automation.

## How it Works

This tool bridges the context gap using a **Hybrid Approach**:
1. **Multi-Language Extraction**: The CLI uses language-specific AST processors (Python `ast`, TypeScript `ts-morph`, Go stdlib `ast`, Rust `syn`) to rapidly map classes, functions, types, imports, and relationships without forcing the LLM to waste context tokens loading megabytes of raw text.
2. **Strict Schema Constraints**: The tool scaffolds specific prompt constraints (e.g., `CLAUDE.md` or `.github/copilot-instructions.md`) dictating that your agent *must* act as the overarching librarian for `docs/llm_wiki/`.
3. **Post-Commit Wiki Sync**: A local `.git/hooks/post-commit` script is installed. The sync strategy depends on the agent type:
   - **CLI agents** (`claude`, `aider`, `opencode`): every commit spawns a fully detached background process that captures the `git diff`, merges it with the structural AST, and invokes the agent headlessly to update the wiki automatically.
   - **IDE agents** (`copilot`, `cursor`, `generic`): every commit generates a ready-to-paste sync prompt at `.git/llm-wiki-prompt.txt`. You paste it into your IDE chat to trigger the update.

## Agent Support

| Agent | Schema file | Auto-sync mode |
|---|---|---|
| `claude` | `CLAUDE.md` | Headless background process |
| `aider` | `.aider.conf.yml` | Headless background process |
| `opencode` | `.opencode/instructions.md` | Headless background process |
| `copilot` | `.github/copilot-instructions.md` | IDE prompt (paste into chat) |
| `cursor` | `.cursorrules` | IDE prompt (paste into chat) |
| `generic` | `.agents.md` | IDE prompt (paste into chat) |

## Multi-Language Support

The tool supports multiple programming languages via a pluggable extractor architecture:

| Language | Extractor | Requirements | Installation |
|----------|-----------|--------------|--------------|
| **Python** | AST (stdlib) | Python 3.9+ | Included |
| **TypeScript** | ts-morph (Node.js) | Node.js 18+, npm | `pip install llm-wiki-cli[typescript]` |
| **Go** | stdlib `ast` | Go 1.21+ | Included (auto-detects from PATH) |
| **Rust** | syn + cargo | Rust toolchain | Included (auto-compiles on first use) |

All extractors share the same output format and are automatically invoked by `bootstrap`, `extract`, `lint`, and `sync` commands.

Each language provides:
- **Classes/Types** → Entity wiki pages with attributes, methods, relationships
- **Functions/Methods** → Function tables in module pages
- **Imports** → Cross-module relationship tracking
- **Docstrings/Comments** → Included in entity documentation

## Installation (with Multi-Language Support)

Basic (Python only):
```bash
pip install llm-wiki-cli
```

TypeScript/JavaScript support:
```bash
pip install llm-wiki-cli[typescript]
```

All languages:
```bash
pip install llm-wiki-cli[typescript,go,rust]
```

Or from source:
```bash
git clone https://github.com/Denissvgn/python-wiki-llm.git
cd python-wiki-llm
pip install -e ".[typescript,go,rust]"
```

## Setup & Initialization

Bootstrap the wiki and agent constraint schema inside the root of your project:

```bash
llm-wiki init --agent claude
```

Supported agents: `claude`, `aider`, `opencode`, `copilot`, `cursor`, `generic`.

**What this does**:
- Creates `docs/llm_wiki/index.md` (table of contents).
- Creates `docs/llm_wiki/log.md` (append-only chronological ledger).
- Scaffolds `entities/`, `modules/`, `workflows/`, and `infrastructure/` directories.
- Writes the agent-specific instruction file (e.g. `CLAUDE.md`, `.github/copilot-instructions.md`) so the agent knows the rules of the system.
- Saves the chosen agent to `.git/.llm-wiki-agent` (local-only, not committed) so subsequent commands (like `install-hook`) pick it up automatically.
- Adds llm-wiki temp files to `.gitignore` (`.git/llm-wiki-*.txt`, `.lock`, `.json`, `.log`).

> If you pass a CLI agent (`claude`, `aider`, `opencode`) that is not installed on your `PATH`, `init` will warn you but still create all files.

Use `--wiki-dir` to change the default wiki location:

```bash
llm-wiki init --agent copilot --wiki-dir .wiki
```

Disable quality hints (agent constraints for surgical changes and careful editing):
```bash
llm-wiki init --agent copilot --no-quality-hints
```

## Bootstrap an Existing Codebase

Generate a comprehensive wiki from an existing project in one command:

```bash
llm-wiki bootstrap --src-dir . --wiki-dir docs/llm_wiki
```

**What this does**:
- Scans all project files via **multi-language AST extraction** (Python, TypeScript, Go, Rust).
- For each language:
  - Python: deep extraction (docstrings, attributes with types/defaults, method signatures, decorators, imports).
  - TypeScript/Go/Rust: classes, interfaces, types, functions, methods, imports.
- Creates **entity pages** (`entities/<ClassName>.md`) with full attribute tables, method signatures, and cross-module relationship links.
- Creates **module pages** (`modules/<filename>.md`) with import tables, class summaries, and function signatures with decorators.
- Discovers and documents **Docker/Compose files** as `infrastructure/<name>.md` with build stages, ports, environment variables, volumes, services, and cross-references to source code.
- Rebuilds `index.md` and appends a summary to `log.md`.
- Creates a `.llm-wiki-manifest.json` file for incremental syncs (see `llm-wiki sync` below).
- Cross-references imports to build `used_by` / `imported_by` relationship graphs between entities.

**Flags**:
- `--overwrite` — Regenerate existing pages instead of skipping them.
- `--depth shallow|full` — `full` (default) extracts everything; `shallow` produces name-only stubs.

**Multi-language support:**
- **Python**: Always available (stdlib `ast`)
- **TypeScript** (`.ts`, `.tsx`): Install optional dependency: `pip install llm-wiki-cli[typescript]`
- **Go** (`.go`): Requires Go 1.21+ on PATH
- **Rust** (`.rs`): Requires Cargo on PATH; compiles on first use

## Automation Setup (Highly Recommended)

Install the post-commit hook to keep the wiki in sync automatically:

```bash
llm-wiki install-hook
```

The agent is read automatically from `.git/.llm-wiki-agent` (written by `init` as a local-only, non-committed file). You can override it:

```bash
llm-wiki install-hook --agent aider
llm-wiki install-hook --wiki-dir .wiki        # custom wiki dir
```

### CLI Agents (Claude, Aider, OpenCode)

The post-commit hook spawns `llm-wiki trigger-agent` as a detached background process via `nohup`:

1. Calculates `git diff HEAD~1..HEAD`.
2. Parses the Python project for Class/Function AST models via `llm-wiki extract`.
3. Writes a temporary command payload to `.git/llm-wiki-prompt.txt`.
4. Spawns the CLI agent (e.g., `claude -p --dangerously-skip-permissions`) and pipes the prompt in.
5. The agent updates the `docs/llm_wiki/` markdown files and commits the result.

Inspect the background log at any time:
```bash
cat .git/llm-wiki-sync.log
```

### IDE Agents (Copilot, Cursor, Generic)

Because IDE agents run inside the editor and have no headless CLI interface, the post-commit hook generates a sync prompt instead:

1. Calculates the diff + AST context.
2. Writes the ready-to-paste prompt to `.git/llm-wiki-prompt.txt`.
3. Prints a reminder in the terminal.

After every commit you'll see:
```
╔══════════════════════════════════════════════════════════════╗
║  LLM Wiki: paste the sync prompt into your IDE agent chat.  ║
║  File: .git/llm-wiki-prompt.txt                             ║
╚══════════════════════════════════════════════════════════════╝
```

Paste the file contents into your agent chat to trigger the wiki update.

You can also generate the prompt manually at any time (without committing):
```bash
llm-wiki generate-prompt
llm-wiki generate-prompt --print              # print to stdout
llm-wiki generate-prompt --wiki-dir .wiki     # custom wiki dir
```

### Auto Version Bumping (Opt-In)

Enable automatic semantic version bumping on commit and push:

```bash
llm-wiki install-hook --enable-versioning
```

This installs additional hooks (disabled by default):
- **pre-commit** → Patch bump on every commit (`0.1.5` → `0.1.6`)
- **pre-push** → Minor bump on every push (`0.1.6` → `0.2.0`, resets patch)

Supported version files: `pyproject.toml`, `setup.cfg`, `package.json`, `VERSION`.

Recursion guards prevent infinite loops — the push-time commit skips the patch hook, and the re-push skips the pre-push hook.

You can also bump manually at any time:

```bash
llm-wiki bump --patch          # 0.1.5 -> 0.1.6
llm-wiki bump --minor          # 0.1.6 -> 0.2.0
llm-wiki bump --patch --stage  # bump + git add (for hook use)
```

## Manual Commands

You or your agent can manually invoke any part of the pipeline:

### 1. Structural Extraction

Extracts the project topology into a token-friendly JSON representation (all languages):
```bash
llm-wiki extract --src-dir .
llm-wiki extract --src-dir . --changed        # only files changed in last commit
llm-wiki extract --src-dir . --summary        # compact output (names only)
llm-wiki extract --src-dir . --paths src/foo.py src/bar.py  # specific files
```

**Flags**:
- `--changed` — Extract only files modified since the last commit (for large projects)
- `--summary` — Compact format with class/function names only (no signatures, docstrings)
- `--paths FILE...` — Extract specific files for drill-down detail
- `--deep` — Deep mode (extract nested relationships)

### 2. Linting the Wiki

Validates wiki consistency — checks for broken links, orphan pages, and cross-references all entity/module/infrastructure pages against the live AST to detect undocumented classes, stale pages, and missing modules:
```bash
llm-wiki lint --wiki-dir docs/llm_wiki --src-dir .
```

Returns exit code `1` on any issues, making it CI-compatible.

### 3. Incremental Sync (Fast Updates)

Update the wiki incrementally — only regenerates pages for files that changed since bootstrap/last sync:
```bash
llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki
```

This is much faster than `bootstrap` for large projects. It:
- Creates a `.llm-wiki-manifest.json` file tracking file hashes (local-only, not committed)
- Regenerates entity and module pages only for changed/new files
- Marks deleted files with a deprecation header in their wiki pages
- Rebuilds the index automatically
- Falls back gracefully for pre-manifest wikis (seeds baseline on first run)

### 4. Context Budgeting (Large Projects)

Build a token-budgeted snapshot of the codebase for feeding to agents when the full extract is too large:
```bash
llm-wiki context --budget 8000 --src-dir . --format markdown
llm-wiki context --budget 8000 --src-dir . --format json
llm-wiki context --budget 8000 --focus changed   # prioritise changed files
llm-wiki context --budget 8000 --focus all       # treat all files equally
```

**Flags**:
- `--budget TOKENS` (required) — Maximum token count for output
- `--format markdown|json` — Output format (default: json)
- `--focus changed|all` — Priority classification (changed files get full detail; default: changed)

### 5. Legacy Wiki Migration

Reconcile pages generated by older llm-wiki versions with the current
collision-aware naming rules without deleting prior content:
```bash
llm-wiki migrate --src-dir . --wiki-dir docs/llm_wiki
llm-wiki migrate --dry-run                    # preview without writing
llm-wiki migrate --chunk-size 200 --plan-chunks  # inspect chunk plan
llm-wiki migrate --chunk-size 200             # apply next pending chunk
```

This regenerates active canonical pages, preserves previous page content under
`## Legacy Notes`, archives old pages under `docs/llm_wiki/legacy/`, rebuilds
`index.md`, refreshes the sync manifest, and rewrites known active links.
Archived `legacy/` pages are ignored by `lint`.

For large wikis, use `--chunk-size` to keep each working-tree change small.
Run the same chunked command repeatedly, reviewing or committing between runs.
The final chunk refreshes `index.md`, active links, and `.llm-wiki-manifest.json`.

### 6. Generate Sync Prompt (IDE agents)

Builds the diff + AST sync prompt and writes it to a file for pasting into your IDE agent chat:
```bash
llm-wiki generate-prompt
llm-wiki generate-prompt --print              # print to stdout instead
llm-wiki generate-prompt --output my.txt     # custom output path
```

### 7. Upgrade Framework

Refresh all framework-managed artifacts in one command (idempotent, non-destructive):
```bash
llm-wiki upgrade
llm-wiki upgrade --agent copilot              # switch agents
llm-wiki upgrade --wiki-dir .wiki             # custom wiki dir
llm-wiki upgrade --no-quality-hints           # disable quality hints
```

This updates:
- Agent constraint blocks in schema files
- Wiki directory structure (adds missing directories)
- Git hooks (if previously installed)
- `.gitignore` entries

### 8. Project Status

Display the current wiki setup and integration status:
```bash
llm-wiki status
```

Shows: wiki directory, configured agent, installed hooks, circuit breaker state, page counts.

### 9. Version Bump

Manually bump the project version:
```bash
llm-wiki bump --patch   # increment patch
llm-wiki bump --minor   # increment minor, reset patch
```

## Wiki File Naming Conventions

The wiki uses collision-aware naming to ensure every page has a unique filename:

| Page Type | Pattern | Examples |
|-----------|---------|----------|
| **Entity** | `entities/<ClassName>.md` | `User.md`, `parser_Parser.md` (when collision) |
| **Module** | `modules/<file_stem>.md` | `cli.md`, `pkg_a_cli.md` (when collision) |
| **Workflow** | `workflows/<name>.md` | `user_auth_flow.md` |
| **Infrastructure** | `infrastructure/<path_transformed>.md` | `Dockerfile.md`, `test_project_Dockerfile.md`, `docker-compose_yml.md` |

**Collision-aware naming:**
- When multiple classes share the same name across different files, the module page name is prepended (e.g., `pkg_a_cli_Parser.md` vs `pkg_b_cli_Parser.md`)
- When multiple files share the same stem in different directories, parent directory components are progressively added (e.g., `pkg_a_cli.md` vs `pkg_b_cli.md`)
- These rules are automatically enforced by `bootstrap`, `sync`, and validated by `lint`

## Uninstalling from a Project

Remove LLM Wiki integration artifacts (hooks, agent constraint blocks, temp files) while **preserving the wiki documentation**:

```bash
llm-wiki uninstall
```

To also delete the wiki documentation directory:
```bash
llm-wiki uninstall --remove-wiki
```

Preview what would be removed first:
```bash
llm-wiki uninstall --dry-run
```

**Safety guarantees:**
- **Wiki docs**: kept by default. Pass `--remove-wiki` to opt-in to deletion.
- **Agent schema files** (e.g. `CLAUDE.md`): only the `# --- LLM Wiki Maintainer Constraints ---` block is stripped. Any user-written content outside that block is preserved. The file is only deleted if it contained nothing else.
- **Git hooks**: only removed if they contain the `LLM Wiki` signature. Custom user hooks are never touched.
- The CLI itself is not uninstalled — run `pip uninstall llm_wiki_cli` separately if needed.
