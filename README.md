# LLM Wiki CLI

A companion CLI designed to help Native LLM Coding Agents (like Claude Code, OpenCode, Cursor, Copilot, or Aider) autonomously maintain a persistent architectural memory ("Wiki") of your Python projects.

By providing constant, up-to-date documentation via a local wiki, your LLM agents will stop rediscovering project boundaries from scratch upon every interaction. Instead, the agent learns to consult the `docs/llm_wiki` first, and updates it gracefully whenever a commit alters the software architecture.

> Inspired by Andrej Karpathy's post on [LLM-native development workflows](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

> **Warning:** This tool grants **full unsupervised permissions** to background agents (e.g. `--dangerously-skip-permissions` for Claude Code). The post-commit hook runs headlessly with no human-in-the-loop confirmation. Use with caution — review your agent's capabilities and ensure you trust the execution environment before enabling automation.

## How it Works

This tool bridges the context gap using a **Hybrid Approach**:
1. **Extraction**: The CLI uses native `ast` processing to rapidly map Pydantic models, class inheritance, attributes, method signatures, decorators, imports, and top-level functions without forcing the LLM to waste context tokens loading megabytes of raw text.
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

Bootstrap the wiki and agent constraint schema inside the root of your project:

```bash
llm-wiki init --agent claude
```

Supported agents: `claude`, `aider`, `opencode`, `copilot`, `cursor`, `generic`.

**What this does**:
- Creates `docs/llm_wiki/index.md` (table of contents).
- Creates `docs/llm_wiki/log.md` (append-only chronological ledger).
- Scaffolds `entities/`, `modules/`, and `workflows/` directories.
- Writes the agent-specific instruction file (e.g. `CLAUDE.md`, `.github/copilot-instructions.md`) so the agent knows the rules of the system.
- Saves the chosen agent to `docs/llm_wiki/.llm-wiki-agent` so subsequent commands (like `install-hook`) pick it up automatically.

> If you pass a CLI agent (`claude`, `aider`, `opencode`) that is not installed on your `PATH`, `init` will warn you but still create all files.

Use `--wiki-dir` to change the default wiki location:

```bash
llm-wiki init --agent copilot --wiki-dir .wiki
```

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

Install the post-commit hook to keep the wiki in sync automatically:

```bash
llm-wiki install-hook
```

The agent is read automatically from `docs/llm_wiki/.llm-wiki-agent` (written by `init`). You can override it:

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
Extracts the project topology into a token-friendly JSON representation:
```bash
llm-wiki extract --src-dir .
```

### 2. Linting the Wiki
Validates wiki consistency — checks for broken links, orphan pages, and cross-references all entity/module pages against the live AST to detect undocumented classes, stale pages, and missing modules:
```bash
llm-wiki lint --wiki-dir docs/llm_wiki --src-dir .
```

Returns exit code `1` on any issues, making it CI-compatible.

### 3. Generate Sync Prompt (IDE agents)
Builds the diff + AST sync prompt and writes it to a file for pasting into your IDE agent chat:
```bash
llm-wiki generate-prompt
llm-wiki generate-prompt --print              # print to stdout instead
llm-wiki generate-prompt --no-diff           # skip git diff (e.g. no commits yet)
llm-wiki generate-prompt --output my.txt     # custom output path
```

### 4. Version Bump
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
