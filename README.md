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
- `flows/`: user-flow pages, one per detected entry point (public API,
  framework-decorated CLI/HTTP/MCP handlers, `__main__`/console scripts), each
  with a Mermaid sequence diagram of the resolved call path.
- `infrastructure/`: Dockerfile and Compose pages.
- `dependencies.md` and `load-order.md`: optional architecture pages for the
  internal dependency graph, import cycles, external dependency reconciliation,
  and load-order caveats.
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
| `claude` | `CLAUDE.md` | prompt hook; optional manual CLI trigger |
| `aider` | `.aider.conf.yml` | prompt hook; optional manual CLI trigger |
| `opencode` | `.opencode/instructions.md` | prompt hook; optional manual CLI trigger |
| `copilot` | `.github/copilot-instructions.md` | IDE prompt |
| `cursor` | `.cursorrules` | IDE prompt |
| `generic` | `AGENTS.md` | IDE prompt |

Installed hooks generate a reviewed prompt file for all agents. The explicit
`trigger-agent` command can still delegate to a CLI agent; for Claude, this uses
`claude -p` and leaves permission decisions to Claude's normal permission model.
Run manual CLI triggers only in repositories and execution environments you
trust.

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

`llm-wiki install-hook` installs a `post-commit` hook that generates
`.git/llm-wiki-prompt.txt` with `llm-wiki generate-prompt` and prints a reminder
to paste that prompt into your agent chat. Generated hooks never launch CLI
agents automatically.

For advanced trusted workflows, `trigger-agent` remains available as an explicit
manual command:

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
llm-wiki bootstrap --skip-flows
llm-wiki bootstrap --skip-dependencies
llm-wiki bootstrap --format json --source-adapter
```

`bootstrap` writes entity, module, workflow, flow, infrastructure, index, log,
dependency architecture, and manifest files. User-flow pages under `flows/` are
generated from detected entry points with a call sequence, generated static
`## Data flow` section, boundary-effects table, and editable `## Behavior`; use
`--skip-flows` to omit them.
Dependency architecture pages are generated as `dependencies.md` and
`load-order.md`; use `--skip-dependencies` for projects that do not want those
pages or lint diagnostics. `--depth full` is the default and includes
docstrings, imports, attributes, method signatures, and relationship data where
extractors provide it. Use `--source-adapter` when callers need bootstrap to
write only under `--wiki-dir`; this skips agent constraint-file updates outside
the generated wiki directory. Use `--format json` to emit a machine-readable
summary with created, updated, and skipped files plus source counts and the
manifest path.

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
parallel extraction for built-in languages and plugin extractors whose manifests
set `"parallel_safe": true`. Sync repairs manifests with invalid source hashes
without touching pages, and stops unusually broad diffs unless `--force` is used.

`sync` is deterministic: it updates AST/docstring-based page skeletons and does
not call an LLM. In agent workflows, treat sync as the first step, then inspect
created or updated pages and replace generic `_Auto-generated from ..._`,
copied-docstring-only, or knowable `—` placeholders with project-specific
semantic explanations.

When `dependencies.md` or `load-order.md` already exists, `sync` also
regenerates those architecture pages from the current dependency inventory and
keeps their human-authored `## Notes` sections unless `--no-preserve-semantic`
is set. Those notes are the agent's responsibility: document intentional cycles,
dynamic imports, side effects, and notable dependency rationale. Projects
bootstrapped with `--skip-dependencies`, or older wikis without those pages,
stay untouched.

When flow pages already exist, `sync` also refreshes generated call-sequence and
`## Data flow` content from the current inventory while preserving the
human-authored `## Behavior` section by default.

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
llm-wiki extract --src-dir . --summary --output sources/code.json --read-only
llm-wiki extract --src-dir /path/to/repo --allow-external-src --summary
```

The JSON output includes `schema_version: "llm-wiki-extract/v1"` plus
`inventory` and optional `docker` objects. With `--deep`, Python function entries
may carry optional `data_effects` blocks (inputs, selected global/attribute
reads, writes, returns, and boundary effects such as filesystem, environment,
process, network, output, and logging calls) and optional `calls` lists (in-body
call targets, optionally with compact `args` and `kwargs` expression summaries).
The payload also gains an optional top-level `entrypoints` array (detected
user-reachable entry points: `{id, category, file, symbol, label}`), a
`data_flows` list for detected user flows, plus a top-level `dependencies`
object with internal `edges`, `cycles`, per-language external dependency
reconciliation, and `load_order`. When `--deep` is combined with `--changed`,
`--paths`, `--package`, or `--summary`, `data_flows` and `dependencies` describe
the emitted inventory before summary collapse. Inventory keys are POSIX paths relative to `--src-dir`,
never absolute paths. The v1 contract permits additive fields; incompatible
shape changes require a new schema version.

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
`cache` object. Use `--jobs N` or `--jobs auto` to opt into parallel extraction
for built-in languages and plugin extractors whose manifests set
`"parallel_safe": true`; the default is `--jobs 1`. Plugin extractors without
that opt-in remain sequential.

When dependency architecture pages exist, lint reruns dependency analysis and
surfaces import cycles, undeclared dependencies, and unused declared
dependencies as warning diagnostics. These warnings are visible in human output
and profile JSON but do not make `lint`, `lint --strict`, or `ci-check` fail by
themselves. Stale architecture pages with no current source modules remain hard
issues.
When flow pages exist, lint also reports generated data-flow gaps, such as
unresolved calls that static analysis cannot classify, as warning diagnostics.

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
llm-wiki context --budget 12000 --format json --focus all --output context.json --read-only
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

`--output PATH` writes the generated JSON or Markdown directly instead of
printing it to stdout. `--read-only` documents source-adapter intent: the command
does not write wiki files, hooks, manifests, local config, or helper/cache state,
except for an explicit `--output` artifact.

### Codebase source integration

For research or indexing systems that need codebase evidence without adopting
the maintained wiki format, prefer the read-only source-adapter commands:

```bash
llm-wiki extract --src-dir <repo> --summary --read-only
llm-wiki context --src-dir <repo> --budget 12000 --format json --focus all --read-only
llm-wiki bootstrap --src-dir <repo> --wiki-dir sources/code_wikis/<source_id> --format json --source-adapter
```

By default, `--src-dir` must resolve inside the current working directory. For a
trusted source tree outside cwd, pass `--allow-external-src`; explicit
`--paths` are still constrained to the chosen source root. Explicit output paths
such as `--output` may be absolute or outside the project root because they are
caller-selected artifacts.

Example `extract --summary` payload:

```json
{
  "schema_version": "llm-wiki-extract/v1",
  "inventory": {
    "models.py": {
      "language": "python",
      "package": "sample",
      "classes": ["User"],
      "functions": ["load_user"]
    }
  }
}
```

Example `context --format json` payload:

```json
{
  "budget": 12000,
  "used": 320,
  "truncated": false,
  "omitted_files": [],
  "downgraded_files": {},
  "files": {
    "models.py": {
      "priority": "high",
      "detail": "deep",
      "classes": [{"name": "User"}],
      "functions": []
    }
  }
}
```

Example `bootstrap --format json --source-adapter` summary:

```json
{
  "schema_version": "llm-wiki-bootstrap-summary/v1",
  "src_dir": "/path/to/repo",
  "generated_wiki_path": "sources/code_wikis/repo",
  "depth": "full",
  "source_files": 12,
  "classes": 8,
  "functions": 31,
  "docker_files": 1,
  "workflows": 2,
  "cross_references": 14,
  "created_files": ["sources/code_wikis/repo/index.md"],
  "updated_files": [],
  "skipped_files": [],
  "manifest_path": "sources/code_wikis/repo/.llm-wiki-manifest.json"
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
`.llm-wiki/catalog.json`. Extractor and lint-rule entry points must resolve to
Python files inside the plugin directory; installed entry points are checked
again before runtime import. Extractor components may set
`"parallel_safe": true` to opt into `--jobs` parallel execution; omit it unless
the extractor is safe to run concurrently in a fresh instance.

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

Manual CLI triggers can edit files and run commands according to the selected
agent's own permission model. Review generated prompt files and wiki diffs
before trusting agent-produced changes in a shared repository.

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
