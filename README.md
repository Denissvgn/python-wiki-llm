# LLM Wiki CLI

LLM Wiki CLI builds and maintains a repo-local architectural wiki for coding
agents. It scans source code into a compact structural inventory, generates
Markdown pages under a wiki directory, validates those pages against the live
codebase, and prepares or triggers wiki-sync prompts after commits.

The PyPI distribution is `agent-wiki-cli`. The installed console command remains
`llm-wiki`, and the Python import package remains `llm_wiki_cli`.

## What It Creates

The default wiki lives at `docs/llm_wiki/` and contains:

- `index.md`: table of contents for generated pages.
- `log.md`: append-only architectural change log.
- `entities/`: class, struct, interface, and type pages.
- `modules/`: source-file pages.
- `workflows/`: detected or manually maintained cross-module flow pages.
- `infrastructure/`: Dockerfile and Compose pages.
- `.llm-wiki-manifest.json`: source hash manifest used by incremental sync and strict linting.

The package has no required Python runtime dependencies. Optional features use
external tools when they are available on `PATH`.

## Supported Inputs

| Area | Implementation | Runtime requirement |
|---|---|---|
| Python | stdlib `ast` | Python 3.9+ |
| TypeScript / TSX | bundled Node script using `ts-morph` | prepared Node.js dependencies |
| Go | bundled Go extractor using `go/ast` | prepared helper binary |
| Rust | bundled Rust extractor using `syn` | prepared helper binary |
| Docker / Compose | built-in parsers | none |
| MCP server | official Python MCP SDK | `agent-wiki-cli[mcp]`, Python 3.10+ |

TypeScript, Go, and Rust extras are metadata-only; prepare their helper
dependencies explicitly with `llm-wiki prepare-extractors`. Lint, CI, and
extract never run `npm install`, `go build`, `go run`, `cargo build`, or
`cargo run` automatically.

## Agent Support

| Agent | Schema file | Sync mode |
|---|---|---|
| `claude` | `CLAUDE.md` | headless CLI |
| `aider` | `.aider.conf.yml` | headless CLI |
| `opencode` | `.opencode/instructions.md` | headless CLI |
| `copilot` | `.github/copilot-instructions.md` | IDE prompt |
| `cursor` | `.cursorrules` | IDE prompt |
| `generic` | `AGENTS.md` | IDE prompt |

Headless sync delegates to the selected CLI agent. For Claude, this currently
uses `claude -p --dangerously-skip-permissions`, so enable automation only in an
environment where that is acceptable.

## Installation

From PyPI:

```bash
pip install agent-wiki-cli
```

With MCP server support:

```bash
pip install "agent-wiki-cli[mcp]"
```

From source:

```bash
git clone https://github.com/Denissvgn/python-wiki-llm.git
cd python-wiki-llm
pip install -e ".[dev]"
```

The following extras are accepted for compatibility with documented workflows,
but they do not install the external TypeScript, Go, or Rust toolchains:

```bash
pip install "agent-wiki-cli[typescript,go,rust]"
```

Uninstall the Python package with:

```bash
pip uninstall agent-wiki-cli
```

## Quick Start

Initialize the wiki structure and the agent instruction file:

```bash
llm-wiki init --agent claude
```

Generate the initial wiki from an existing codebase:

```bash
llm-wiki bootstrap --src-dir . --wiki-dir docs/llm_wiki
```

Validate the wiki:

```bash
llm-wiki lint --wiki-dir docs/llm_wiki --src-dir .
```

Install a post-commit hook:

```bash
llm-wiki install-hook
```

`init` writes the selected agent and quality-hint setting to
`.git/.llm-wiki-agent` when the project is a Git repo. Outside Git, it falls
back to `<wiki-dir>/.llm-wiki-agent`.

## Automation

`llm-wiki install-hook` installs a `post-commit` hook. The hook mode depends on
the configured agent.

For CLI agents (`claude`, `aider`, `opencode`), the hook starts:

```bash
llm-wiki trigger-agent --agent <agent>
```

The trigger command:

- takes `git diff HEAD~1..HEAD`;
- skips empty diffs and oversized diffs unless `--force` is used;
- uses a lock file to prevent concurrent syncs;
- opens a circuit breaker after repeated failures;
- builds deep source inventory and call-graph context;
- writes `.git/llm-wiki-prompt.txt` with owner-only permissions where supported;
- invokes the selected agent with a prompt that asks it to update, lint, and commit wiki changes.

Useful trigger options:

```bash
llm-wiki trigger-agent --agent claude --timeout 600 --max-diff-lines 2000
llm-wiki trigger-agent --agent claude --max-prompt-bytes 2000000
llm-wiki trigger-agent --agent claude --force
llm-wiki trigger-agent --reset-breaker
```

For IDE agents (`copilot`, `cursor`, `generic`), the hook generates
`.git/llm-wiki-prompt.txt` with `llm-wiki generate-prompt` and prints a reminder
to paste that prompt into the IDE chat.

Optional strict pre-commit validation:

```bash
llm-wiki install-hook --enable-validation
```

Use `--force` when you intentionally want to replace an existing unrelated hook:

```bash
llm-wiki install-hook --force
```

## Command Reference

### `init`

Scaffold the wiki structure and agent constraint file.

```bash
llm-wiki init --agent claude
llm-wiki init --agent copilot --wiki-dir .wiki
llm-wiki init --agent cursor --no-quality-hints
```

Supported agents are `claude`, `aider`, `opencode`, `copilot`, `cursor`, and
`generic`.

### `bootstrap`

Generate a full wiki for an existing project.

```bash
llm-wiki bootstrap --src-dir . --wiki-dir docs/llm_wiki
llm-wiki bootstrap --overwrite
llm-wiki bootstrap --depth shallow
llm-wiki bootstrap --skip-workflows
```

`bootstrap` writes entity, module, workflow, infrastructure, index, log, and
manifest files. `--depth full` is the default and includes docstrings, imports,
attributes, method signatures, and relationship data where extractors provide
it.

### `sync`

Incrementally regenerate only pages whose source files changed since the last
manifest.

```bash
llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki
llm-wiki sync --jobs auto --cache-stats --src-dir . --wiki-dir docs/llm_wiki
```

If an older wiki has `index.md` but no manifest, `sync` seeds
`.llm-wiki-manifest.json` without modifying pages. If neither a manifest nor an
existing wiki is present, run `bootstrap` first. Sync uses the same safe
persistent inventory cache as lint when a git directory is available. Use
`--no-cache`, `--rebuild-cache`, `--cache-dir PATH`, and `--cache-stats` to
control or inspect cache behavior. Use `--jobs N` or `--jobs auto` to opt into
parallel built-in language extraction. Sync repairs manifests with invalid
source hashes without touching pages, and stops unusually broad diffs unless
`--force` is used.

`sync` is deterministic: it updates AST/docstring-based page skeletons and does
not call an LLM. In agent workflows, treat sync as the first step, then inspect
created or updated pages and replace generic `_Auto-generated from ..._`,
copied-docstring-only, or knowable `—` placeholders with project-specific
semantic explanations.

### `extract`

Print source inventory as JSON. All registered extractors run; missing optional
prepared helpers are skipped when there are no matching source files.

```bash
llm-wiki extract --src-dir .
llm-wiki extract --src-dir . --changed
llm-wiki extract --src-dir . --summary
llm-wiki extract --src-dir . --deep
llm-wiki extract --src-dir . --paths src/foo.py src/bar.ts
llm-wiki extract --src-dir . --package llm_wiki_cli
llm-wiki extract --src-dir . --include-empty
```

### `prepare-extractors`

Prepare TypeScript dependencies and cached Go/Rust helper binaries outside the
lint/extract hot path.

```bash
llm-wiki prepare-extractors --src-dir .
llm-wiki prepare-extractors --language typescript --language go
llm-wiki prepare-extractors --cache-dir .cache/llm-wiki
```

When `--language` is omitted, only helper languages detected in `--src-dir` are
prepared. Helper cache resolution follows `--cache-dir`, then
`LLM_WIKI_CACHE_DIR`, then `.git/llm-wiki-extractors/`. If Go is installed in a
nonstandard location or the `go` on `PATH` cannot run, set
`LLM_WIKI_GO=/path/to/go` before running `prepare-extractors`.

### `lint` and `ci-check`

Validate wiki links, orphan pages, entities, modules, workflows,
infrastructure, plugin lint rules, and team policy.

```bash
llm-wiki lint --wiki-dir docs/llm_wiki --src-dir .
llm-wiki lint --strict --wiki-dir docs/llm_wiki --src-dir .
llm-wiki lint --profile --wiki-dir docs/llm_wiki --src-dir .
llm-wiki lint --cache-stats --wiki-dir docs/llm_wiki --src-dir .
llm-wiki lint --jobs auto --wiki-dir docs/llm_wiki --src-dir .
```

Strict mode also requires the core wiki structure and a fresh sync manifest.
`--profile` suppresses the human-readable lint text and prints one JSON object
to stdout containing the normal lint report, diagnostics, and phase timings.
The JSON contract is preserved for extractor failures as well; lint still exits
nonzero, but stdout remains machine-readable.
Lint uses a persistent deep-inventory cache by default when a git directory is
available, storing `.git/llm-wiki-inventory-cache.json`. Override the cache
directory with `LLM_WIKI_CACHE_DIR` or `--cache-dir PATH`; the CLI flag wins.
Use `--no-cache` to disable load/save, `--rebuild-cache` to ignore and rewrite
the cache, and `--cache-stats` to include cache diagnostics. Cache corruption or
invalid fingerprints fall back to a full extraction without reducing lint
coverage. With `--profile --cache-stats`, the JSON payload includes a top-level
`cache` object. Use `--jobs N` or `--jobs auto` to opt into parallel built-in
language extraction; the default is `--jobs 1`. Plugin extractors remain
sequential unless future plugin metadata explicitly marks them parallel-safe.

For CI:

```bash
llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki
llm-wiki ci-check --jobs auto --src-dir . --wiki-dir docs/llm_wiki
llm-wiki ci-check --format json --report .git/llm-wiki-ci-report.md
llm-wiki ci-check --format markdown
```

`ci-check` always runs strict validation, writes a Markdown report, records a
local metrics event, uses the same safe inventory cache when available, and
exits nonzero on validation failure. `--report` is an output path, so explicit
absolute paths and relative artifact paths outside the project root are allowed.

### `context`

Build a token-budgeted source snapshot for agents.

```bash
llm-wiki context --budget 8000 --src-dir . --format json
llm-wiki context --budget 8000 --src-dir . --format markdown
llm-wiki context --budget 8000 --focus changed
llm-wiki context --budget 8000 --focus all
```

`--focus changed` is the default. Changed files get full detail, one-hop import
neighbors get slim detail, and remaining files get names only.

External tools can use the `llm-wiki-context/v1` JSON request protocol:

```bash
llm-wiki context --request request.json --src-dir .
cat request.json | llm-wiki context --request - --src-dir .
```

Example request:

```json
{
  "protocol": "llm-wiki-context/v1",
  "budget_tokens": 8000,
  "focus": ["changed", "neighbors"],
  "format": "json",
  "filters": {
    "language": "python"
  }
}
```

### `generate-prompt`

Build a sync prompt for IDE agents or for manual review.

```bash
llm-wiki generate-prompt
llm-wiki generate-prompt --print
llm-wiki generate-prompt --change-type feature
llm-wiki generate-prompt --template compact
```

The generated prompt includes change-type guidance. Installed prompt templates
can override the default prompt body. The default prompt asks agents to run
`sync` first, then perform a semantic pass on affected pages before accepting a
lint-clean wiki as complete.

### `mcp`

Run a local MCP server exposing read-only wiki tools and resources.

```bash
llm-wiki mcp --wiki-dir docs/llm_wiki --src-dir .
llm-wiki mcp --transport http --host 127.0.0.1 --port 8765
```

The MCP server exposes wiki search, entity/module fetches, context payloads,
lint summaries, and status information. HTTP mode is intended for local use and
defaults to loopback.

### `install` and `plugins`

Install and manage local plugins.

```bash
llm-wiki install ./vendor/my-plugin --yes
llm-wiki install my-catalog-plugin --dry-run
llm-wiki plugins list
llm-wiki plugins validate ./vendor/my-plugin
llm-wiki plugins remove my-plugin
```

Plugin manifests can register extractors, prompt templates, lint rules, and
agent skill blocks. Plugin references are resolved from project-local paths or
`.llm-wiki/catalog.json`.

### `team`

Manage shared team policy for prompt defaults, required plugin components, and
generated-wiki conflict handling.

```bash
llm-wiki team init --wiki-dir docs/llm_wiki
llm-wiki team check --src-dir . --wiki-dir docs/llm_wiki
llm-wiki team resolve-conflicts --wiki-dir docs/llm_wiki
llm-wiki team resolve-conflicts --write --wiki-dir docs/llm_wiki
```

`resolve-conflicts` only applies conservative resolutions for generated pages.
Manual workflow conflicts are left for humans to resolve.

### `obsidian`

Export and validate an Obsidian-friendly mirror of the canonical wiki.

```bash
llm-wiki obsidian export --wiki-dir docs/llm_wiki --vault-dir ~/Vaults/project
llm-wiki obsidian check --wiki-dir docs/llm_wiki --vault-dir ~/Vaults/project
llm-wiki obsidian install-plugin --vault-dir ~/Vaults/project
```

The mirror adds frontmatter, wikilinks, related links, and sidecar human notes.
The canonical source of truth remains `docs/llm_wiki/`.

### `metrics`

Show local quality and automation metrics.

```bash
llm-wiki metrics --last 30d
llm-wiki metrics --format json
```

Metrics are stored locally under `.git/llm-wiki-metrics.jsonl` when available.

### `review`

Run a static wiki-aware review of proposed code changes.

```bash
llm-wiki review --base main --head HEAD
llm-wiki review --patch change.patch --format json
```

The review command compares code changes with wiki coverage and reports stale or
missing documentation risks.

### `upgrade`

Refresh framework-managed artifacts in place.

```bash
llm-wiki upgrade
llm-wiki upgrade --agent copilot
llm-wiki upgrade --force
llm-wiki upgrade --no-quality-hints
```

`upgrade` refreshes agent instruction blocks, wiki directories, hooks, plugin
skill blocks, and persisted local config.

### `migrate`

Reconcile older wiki layouts with current canonical names.

```bash
llm-wiki migrate --dry-run
llm-wiki migrate --chunk-size 50 --plan-chunks
llm-wiki migrate --chunk-size 50 --chunk 1
```

### `status`, `release`, `bump`, and `uninstall`

```bash
llm-wiki status
llm-wiki release --stage
llm-wiki bump --patch --stage
llm-wiki uninstall --dry-run
llm-wiki uninstall --remove-wiki
```

`uninstall` removes project integration artifacts. It does not uninstall the
CLI itself. To remove the Python package, run `pip uninstall agent-wiki-cli`.

## Security Model

LLM Wiki is a local automation tool. It can generate prompt files containing
diffs, source structure, and architectural context. Prompt files are written
inside `.git/` by default and use owner-only permissions where the platform
supports that mode.

Headless CLI agents can edit files and run commands according to their own
permission model. Review generated wiki diffs before trusting unattended
automation in a shared repository.

The repository includes community health files:

- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- GitHub issue templates

## Development

Run tests from the repository root:

```bash
pip install -e ".[dev]"
python -m pytest
```

Run the MCP tests with the optional dependency installed:

```bash
pip install -e ".[dev,mcp]"
python -m pytest tests/test_mcp.py
```

Before release, check metadata and docs:

```bash
python -m pytest tests/test_package_metadata.py
python -m build
```

## Contribution Policy

This project does not maintain a formal contribution process. You are welcome to
freely fork it, adapt it to your workflow, and publish your own changes under
the license terms.
