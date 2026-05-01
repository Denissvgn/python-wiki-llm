# LLM Wiki CLI

LLM Wiki CLI builds and maintains a repo-local architectural wiki for coding
agents. It scans source code into a compact structural inventory, generates
Markdown pages under a wiki directory, validates those pages against the live
codebase, and can prepare or trigger wiki-sync prompts after commits.

The default wiki lives at `docs/llm_wiki/` and contains:

- `index.md` - table of contents for generated pages.
- `log.md` - append-only architectural change log.
- `entities/` - class, struct, interface, and type pages.
- `modules/` - source-file pages.
- `workflows/` - detected or manually maintained cross-module flow pages.
- `infrastructure/` - Dockerfile and Compose pages.
- `.llm-wiki-manifest.json` - source hash manifest used by incremental sync and strict linting.

The package has no required Python runtime dependencies. Optional features use
external tools when they are available on `PATH`.

## Supported Inputs

| Area | Implementation | Runtime requirement |
|---|---|---|
| Python | stdlib `ast` | Python 3.9+ |
| TypeScript / TSX | bundled Node script using `ts-morph` | Node.js and npm |
| Go | bundled Go extractor using `go/ast` | Go toolchain |
| Rust | bundled Rust extractor using `syn` | Cargo / Rust toolchain |
| Docker / Compose | built-in parsers | none |
| MCP server | official Python MCP SDK | `llm-wiki-cli[mcp]`, Python 3.10+ |

TypeScript, Go, and Rust extras are metadata-only; the actual toolchains must be
installed separately. The TypeScript extractor runs `npm install` in its bundled
extractor directory on first use if `node_modules` is missing.

## Agent Support

| Agent | Schema file | Sync mode |
|---|---|---|
| `claude` | `CLAUDE.md` | headless CLI |
| `aider` | `.aider.conf.yml` | headless CLI |
| `opencode` | `.opencode/instructions.md` | headless CLI |
| `copilot` | `.github/copilot-instructions.md` | IDE prompt |
| `cursor` | `.cursorrules` | IDE prompt |
| `generic` | `.agents.md` | IDE prompt |

Headless sync delegates to the selected CLI agent. For Claude, this currently
uses `claude -p --dangerously-skip-permissions`, so only enable automation in an
environment where that is acceptable.

## Installation

From PyPI:

```bash
pip install llm-wiki-cli
```

With MCP server support:

```bash
pip install "llm-wiki-cli[mcp]"
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
pip install "llm-wiki-cli[typescript,go,rust]"
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

`init` also appends these runtime files to `.gitignore` when needed:

```text
.git/llm-wiki-prompt.txt
.git/llm-wiki.lock
.git/llm-wiki-breaker.json
.git/llm-wiki-sync.log
.git/llm-wiki-metrics.jsonl
.git/llm-wiki-ci-report.md
```

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
- writes `.git/llm-wiki-prompt.txt`;
- invokes the selected agent with a prompt that asks it to update, lint, and commit wiki changes.

Useful trigger options:

```bash
llm-wiki trigger-agent --agent claude --timeout 600 --max-diff-lines 2000
llm-wiki trigger-agent --agent claude --force
llm-wiki trigger-agent --reset-breaker
```

The installed hook also honors environment variables:

```bash
LLM_WIKI_TIMEOUT=600
LLM_WIKI_MAX_DIFF=2000
```

For IDE agents (`copilot`, `cursor`, `generic`), the hook cannot run the agent
headlessly. It generates `.git/llm-wiki-prompt.txt` with `llm-wiki
generate-prompt` and prints a reminder to paste that prompt into the IDE chat.

Optional strict pre-commit validation:

```bash
llm-wiki install-hook --enable-validation
```

## Commands

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
```

If an older wiki has `index.md` but no manifest, `sync` seeds
`.llm-wiki-manifest.json` without modifying pages. If neither a manifest nor an
existing wiki is present, run `bootstrap` first.

### `extract`

Print source inventory as JSON. All registered extractors run; missing optional
toolchains are skipped with warnings.

```bash
llm-wiki extract --src-dir .
llm-wiki extract --src-dir . --changed
llm-wiki extract --src-dir . --summary
llm-wiki extract --src-dir . --deep
llm-wiki extract --src-dir . --paths src/foo.py src/bar.ts
llm-wiki extract --src-dir . --package llm_wiki_cli
llm-wiki extract --src-dir . --include-empty
```

Flags:

- `--changed` - only files changed in the last commit.
- `--summary` - compact class/function names only.
- `--paths FILE...` - specific source paths relative to `--src-dir`.
- `--deep` - include richer extractor details.
- `--package NAME` - filter by discovered package ownership.
- `--include-empty` - include Python files without tracked components.

### `lint` and `ci-check`

Validate wiki links, orphan pages, entities, modules, workflows,
infrastructure, plugin lint rules, and team policy.

```bash
llm-wiki lint --wiki-dir docs/llm_wiki --src-dir .
llm-wiki lint --strict --wiki-dir docs/llm_wiki --src-dir .
```

Strict mode also requires the core wiki structure and a fresh sync manifest.

For CI:

```bash
llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki
llm-wiki ci-check --format json --report .git/llm-wiki-ci-report.md
llm-wiki ci-check --format markdown
```

`ci-check` always runs strict validation, writes a Markdown report, records a
local metrics event, and exits nonzero on validation failure.

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
  "budget_tokens": 32000,
  "focus": ["changed", "neighbors"],
  "format": "json",
  "filters": {
    "language": "python",
    "module": "llm_wiki_cli.commands.*"
  }
}
```

Supported request fields are `protocol`, `budget_tokens`, `focus`, `format`,
and `filters`. Supported filters are `language` and `module`.

### `generate-prompt`

Build a wiki-sync prompt for IDE agents or manual use.

```bash
llm-wiki generate-prompt
llm-wiki generate-prompt --print
llm-wiki generate-prompt --src-dir . --wiki-dir docs/llm_wiki
llm-wiki generate-prompt --output my-prompt.txt
llm-wiki generate-prompt --change-type bugfix
llm-wiki generate-prompt --template plugin_id/template_id
```

Change types are `auto`, `refactor`, `feature`, `bugfix`, `dependency`, and
`generic`.

### `review`

Run a static wiki-aware review of proposed code changes without invoking an LLM.

```bash
llm-wiki review
llm-wiki review --base main --head HEAD
llm-wiki review --patch change.diff
git diff | llm-wiki review --patch -
llm-wiki review --format json
```

Findings point to changed source files, related wiki pages, and suggested wiki
follow-up.

### `metrics`

Read local metrics from `.git/llm-wiki-metrics.jsonl`.

```bash
llm-wiki metrics --last 30d
llm-wiki metrics --last 7d --format json
llm-wiki metrics --src-dir . --wiki-dir docs/llm_wiki
```

### `bump` and `release`

Update project versions and stamp changelog releases.

```bash
llm-wiki bump --patch
llm-wiki bump --minor
llm-wiki bump --patch --stage
```

Version files supported by the version service are `pyproject.toml`,
`setup.cfg`, `package.json`, and `VERSION`.

```bash
llm-wiki release
llm-wiki release --changelog CHANGELOG.md
llm-wiki release --stage
```

`release` stamps a non-empty `## [Unreleased]` section with the current version
and date, then refreshes GitHub-style reference links when it can infer the repo
URL from existing links.

### `upgrade`

Refresh framework-managed artifacts in place.

```bash
llm-wiki upgrade
llm-wiki upgrade --agent copilot
llm-wiki upgrade --wiki-dir .wiki
llm-wiki upgrade --quality-hints
llm-wiki upgrade --no-quality-hints
```

`upgrade` refreshes schema constraint blocks, wiki directories, installed hooks,
and `.gitignore` entries without deleting user content outside managed blocks.

### `migrate`

Reconcile legacy wiki pages with current collision-aware naming.

```bash
llm-wiki migrate --src-dir . --wiki-dir docs/llm_wiki
llm-wiki migrate --dry-run
llm-wiki migrate --chunk-size 200 --plan-chunks
llm-wiki migrate --chunk-size 200
llm-wiki migrate --chunk-size 200 --chunk 2
```

Migration preserves previous content under `## Legacy Notes`, archives old pages
under `legacy/`, rebuilds `index.md`, refreshes `.llm-wiki-manifest.json`, and
rewrites known active links. Archived `legacy/` pages are ignored by `lint`.

### `install` and `plugins`

Install and manage local llm-wiki plugins.

```bash
llm-wiki install ./plugins/extractor-java --yes
llm-wiki install ./plugins/template-django --dry-run
llm-wiki plugins list
llm-wiki plugins validate ./plugins/template-django
llm-wiki plugins remove extractor-java
```

Plugins are local-only. Direct install paths must stay inside the project root,
or you can resolve names through `.llm-wiki/catalog.json` or
`~/.llm-wiki/catalog.json`. Installed plugins are copied into
`.llm-wiki/plugins/<plugin_id>/` and tracked in `.llm-wiki/plugins.lock.json`.

Supported component types:

- `extractor` - adds a language extractor entry point.
- `lint_rule` - adds a custom lint rule.
- `prompt_template` - adds a `generate-prompt --template` target.
- `skill` - injects a managed skill block into the active agent schema file.

Minimal manifest:

```json
{
  "id": "skill-karpathy-guidelines",
  "version": "0.1.0",
  "llm_wiki_version": "*",
  "components": [
    {
      "type": "skill",
      "id": "guidelines",
      "path": "skills/guidelines/SKILL.md"
    }
  ]
}
```

### `team`

Manage shared team policy and generated-wiki conflict resolution.

```bash
llm-wiki team init --wiki-dir docs/llm_wiki
llm-wiki team check --src-dir . --wiki-dir docs/llm_wiki
llm-wiki team check --format json
llm-wiki team resolve-conflicts --src-dir . --wiki-dir docs/llm_wiki
llm-wiki team resolve-conflicts --write
llm-wiki team resolve-conflicts --format json
```

`team init` writes `.llm-wiki/team.json`. The file is intended to be committed
and can define shared wiki conventions plus required prompt templates, lint
rules, and skills. It does not override each developer's local agent choice in
`.git/.llm-wiki-agent`.

When `.llm-wiki/team.json` exists, `lint`, `ci-check`, and `team check` enforce
the configured policy. `generate-prompt` uses the team default prompt template
unless `--template` is passed.

### `mcp`

Expose the wiki to MCP-compatible agents without giving them direct filesystem
access.

```bash
pip install "llm-wiki-cli[mcp]"
llm-wiki mcp --src-dir . --wiki-dir docs/llm_wiki
llm-wiki mcp --transport http --host 127.0.0.1 --port 8765 --path /mcp
llm-wiki mcp --transport http --allowed-origin http://127.0.0.1:3000
```

The MCP server is local and read-only. It exposes tools for `get_entity`,
`get_module`, `search_wiki`, `get_context`, `check_wiki`, and `get_status`, plus
`llm-wiki://...` resources for index, log, entities, modules, workflows, and
infrastructure. HTTP mode binds only to loopback addresses and rejects
unexpected browser `Origin` headers unless explicitly allowed.

### `obsidian`

Export the canonical wiki into an Obsidian-friendly mirror vault.

```bash
llm-wiki obsidian export --src-dir . --wiki-dir docs/llm_wiki --vault-dir /path/to/vault
llm-wiki obsidian export --vault-dir /path/to/vault --notes-dir .llm-wiki/obsidian-notes
llm-wiki obsidian export --vault-dir /path/to/vault --dry-run --format json
llm-wiki obsidian check --wiki-dir docs/llm_wiki --vault-dir /path/to/vault
llm-wiki obsidian check --vault-dir /path/to/vault --format json
llm-wiki obsidian install-plugin --vault-dir /path/to/vault
llm-wiki obsidian install-plugin --vault-dir /path/to/vault --plugin-dir integrations/obsidian/llm-wiki
```

The mirror is written under `LLM Wiki/` in the vault with Obsidian frontmatter,
aliases, wikilinks, related links, and sidecar human notes. The canonical
`docs/llm_wiki/` files remain the source of truth.

See [integrations/obsidian/llm-wiki/README.md](integrations/obsidian/llm-wiki/README.md)
for desktop plugin development details.

### `status`

Show local setup state.

```bash
llm-wiki status
llm-wiki status --wiki-dir docs/llm_wiki
```

Status reports wiki page counts, configured agent and mode, quality-hint state,
installed LLM Wiki hooks, and circuit-breaker state.

### `uninstall`

Remove LLM Wiki integration artifacts while preserving wiki documentation by
default.

```bash
llm-wiki uninstall
llm-wiki uninstall --dry-run
llm-wiki uninstall --remove-wiki
```

Safety behavior:

- Wiki docs are kept unless `--remove-wiki` is passed.
- Agent schema files are only stripped between managed constraint markers.
- Schema files are deleted only if they contain no user content after stripping.
- Git hooks are removed only when they contain the `LLM Wiki` signature.
- Runtime temp files `.git/llm-wiki-prompt.txt` and `.git/llm-wiki-sync.log` are removed when present.

To uninstall the package:

```bash
pip uninstall llm-wiki-cli
```

## Wiki Naming Rules

Page names are generated to avoid collisions:

| Page type | Pattern | Example |
|---|---|---|
| Entity | `entities/<ClassName>.md` or `entities/<module_page>_<ClassName>.md` | `User.md`, `pkg_a_cli_Parser.md` |
| Module | `modules/<stem>.md` or parent-qualified stem | `cli.md`, `pkg_a_cli.md` |
| Workflow | `workflows/<name>.md` | `checkout_flow.md` |
| Infrastructure | relative path with `/` and `.` replaced by `_` | `Dockerfile.md`, `docker-compose_yml.md` |

These rules are enforced by `bootstrap`, `sync`, `migrate`, and `lint`.

## Development

Run the Python test suite:

```bash
pytest
```

Build the Obsidian plugin during development:

```bash
cd integrations/obsidian/llm-wiki
npm install
npm run dev
```

`main.js` is committed so `llm-wiki obsidian install-plugin` works before a
local rebuild.
