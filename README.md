# LLM Wiki CLI

A companion CLI designed to help Native LLM Coding Agents (like Claude Code, OpenCode, Cursor, or Aider) autonomously maintain a persistent architectural memory ("Wiki") of your Python projects.

By providing constant, up-to-date documentation via a local wiki, your LLM agents will stop rediscovering project boundaries from scratch upon every interaction. Instead, the agent learns to consult the `docs/llm_wiki` first, and updates it gracefully whenever a commit alters the software architecture.

> Inspired by Andrej Karpathy's post on [LLM-native development workflows](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

> **Warning:** This tool grants **full unsupervised permissions** to background agents (e.g. `--dangerously-skip-permissions` for Claude Code). The post-commit hook runs headlessly with no human-in-the-loop confirmation. Use with caution — review your agent's capabilities and ensure you trust the execution environment before enabling automation.

## How it Works

This tool bridges the context gap using a **Hybrid Approach**:
1. **Extraction**: The CLI uses native `ast` processing to rapidly map Pydantic models, class inheritance, attributes, method signatures, decorators, imports, and top-level functions without forcing the LLM to waste context tokens loading megabytes of raw text.
2. **Strict Schema Constraints**: The tool scaffolds specific prompt constraints (e.g., `CLAUDE.md` or `.cursorrules`) dictating that your agent *must* act as the overarching librarian for `docs/llm_wiki/`.
3. **Cross-Agentic Post-Commit Delegation**: A local `.git/hooks/post-commit` script is installed. Every time you (or your agent) commits code, a background process captures the `git diff`, merges it with the structural AST, and **invokes your primary LLM subagent** entirely in the background via the shell (with no human blocking interaction). The subagent then autonomously updates the local markdown wiki files and commits the updates.

## Installation

Inside your Python project's virtual environment:

```bash
pip install llm-wiki-cli

# Or install from source
git clone https://github.com/Denissvgn/python-wiki-llm.git
cd python-wiki-llm
pip install -e .
```

## Setup & Initialization

You must bootstrap the wiki and the agent's constraints schema inside the root of your project:

```bash
llm-wiki init --agent claude
```
*(Supports: `--agent claude`, `--agent cursor`, `--agent copilot`, `--agent generic`)*

**What this does**:
- Creates `docs/llm_wiki/index.md` (The table of contents).
- Creates `docs/llm_wiki/log.md` (The append-only chronological ledger of state changes).
- Scaffolds `entities/`, `modules/`, and `workflows/` directories.
- Writes the specific instruction constraints (e.g. `CLAUDE.md`) in your root directory so the agent knows the rules of the system.

## Bootstrap an Existing Codebase

Generate a comprehensive wiki from an existing project in one command:

```bash
llm-wiki bootstrap --src-dir . --wiki-dir docs/llm_wiki
```

**What this does**:
- Scans all Python files via deep AST extraction (docstrings, attributes with types/defaults, method signatures, decorators, imports).
- Creates **entity pages** (`entities/<ClassName>.md`) with full attribute tables, method signatures, and cross-module relationship links.
- Creates **module pages** (`modules/<filename>.md`) with import tables, class summaries, and function signatures with decorators.
- Rebuilds `index.md` and appends a summary to `log.md`.
- Cross-references imports to build `used_by` / `imported_by` relationship graphs between entities.

**Flags**:
- `--overwrite` — Regenerate existing pages instead of skipping them.
- `--depth shallow|full` — `full` (default) extracts everything; `shallow` produces name-only stubs.

## Automation Setup (Highly Recommended)

To ensure your wiki never falls out of sync with your codebase, install the detached background watcher:

```bash
llm-wiki install-hook
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

### How the Post-Commit Trigger Invokes

When you successfully commit code using `git commit`, the hook spawns the `llm-wiki trigger-agent` process in a detached background state via `nohup`.
1. It calculates `git diff HEAD~1..HEAD`.
2. It parses the Python project for Class/Function AST models via `llm-wiki extract`.
3. It writes a temporary command payload to `.git/llm-wiki-prompt.txt`.
4. It natively spawns your CLI assistant (e.g., `claude --print --prompt-file .git/llm-wiki-prompt.txt`) routing standard input to `/dev/null`.
5. The subagent digests the diff natively, modifies the `docs/llm_wiki/` markdown files, and commits the result.

You can inspect the detached log at any time:
```bash
cat .git/llm-wiki-sync.log
```

## Manual Commands

You or your agent can manually invoke the helper subset:

### 1. Structural Extraction
Extracts the project topology into token-friendly JSON representation:
```bash
llm-wiki extract --src-dir .
```

### 2. Linting the Wiki
Validates wiki consistency — checks for broken links, orphan pages, and cross-references all entity/module pages against the live AST to detect undocumented classes, stale pages, and missing modules:
```bash
llm-wiki lint --wiki-dir docs/llm_wiki --src-dir .
```

Returns exit code `1` on any issues, making it CI-compatible.

### 3. Version Bump
Manually bump the project version:
```bash
llm-wiki bump --patch   # increment patch
llm-wiki bump --minor   # increment minor, reset patch
```

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
