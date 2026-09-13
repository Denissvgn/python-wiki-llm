# LLM Wiki CLI

Build and maintain an architectural wiki for your codebase. LLM Wiki scans
source into Markdown pages, keeps generated structure in sync, and supplies
coding agents with searchable, bounded context. Agents add the explanations
and guides that static analysis cannot provide.

The PyPI package is `agent-wiki-cli`, the command is `llm-wiki`, and the Python
import package is `llm_wiki_cli`.

[Quick start](#quick-start) · [Command reference](docs/cli-reference.md) ·
[Standalone documentation](docs/standalone-documentation.md)

## Installation

Requires Python 3.10 or later.

```bash
pip install agent-wiki-cli
```

For MCP support, install `pip install "agent-wiki-cli[mcp]"`.
[Installation options](docs/wiki-guide.md#installation) cover source checkouts
and optional dependencies. To remove the package, run
`pip uninstall agent-wiki-cli`.

## Quick Start

Run these commands from your project root. Choose `generic` for an `AGENTS.md`
instruction file, or select one of the [supported agents](#agent-support).

```bash
llm-wiki init --agent generic
```

For TypeScript/JavaScript, Go, Rust, or Haskell, first prepare the required
helpers with `llm-wiki prepare-extractors --src-dir .`.
[Helper setup](docs/cli-reference.md#prepare-extractors) is explicit and may
download dependencies or compile a bundled helper. Python needs no helper.

```bash
llm-wiki bootstrap --src-dir . --wiki-dir docs/llm_wiki
```

Open `docs/llm_wiki/index.md` to browse the wiki. Use your coding agent to enrich
semantic descriptions, guides, and behavior notes; generated diagrams, tables,
and machine-readable artifacts are maintained by the CLI.

After source changes, update and validate the wiki:

```bash
llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki --jobs 1
llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki --jobs 1
```

For an isolated documentation workspace from source or an existing enriched
wiki, follow the [standalone documentation guide](docs/standalone-documentation.md).

## What It Creates

The default `docs/llm_wiki/` contains an index, module and entity pages,
workflows, user flows, guides, and a change log. Depending on the source and
options, it also includes infrastructure, API contracts, dependency, and
load-order pages. Generated structure and agent-authored prose share one
canonical wiki.

See the [wiki guide](docs/wiki-guide.md#what-it-creates) for the page taxonomy,
content ownership, generated artifacts, and Python API. Export the same wiki
for [Obsidian](docs/cli-reference.md#obsidian) or a
[static site](docs/cli-reference.md#site).

## Supported Inputs

| Area | Implementation | Runtime requirement |
|---|---|---|
| Python | stdlib `ast` | Python 3.10+ |
| TypeScript / JavaScript / TSX / JSX | `ts-morph` | prepared Node.js dependencies |
| Go | `go/ast` | prepared helper binary |
| Rust | `syn` | prepared helper binary |
| Haskell | GHC parser, syntax-only inventory | prepared helper binary |
| Docker / Compose | built-in parsers | none |
| Runtime/config YAML | targeted built-in parsers | none |
| OpenAPI 3.0/3.1 JSON / YAML | `json` / PyYAML safe loader | included with the package |

Discovery honors `.gitignore`. Use a
[source-selection profile](docs/wiki-guide.md#source-selection) to restrict the
source boundary. See [input details](docs/wiki-guide.md#supported-inputs) for
helper requirements and language-specific behavior.

## Agent Support

Choose `claude`, `aider`, `opencode`, `copilot`, `cursor`, or `generic` during
initialization. Every agent can use explicit sync, lint, and reviewed prompts;
LLM Wiki does not install Git hooks.

[Agent setup](docs/wiki-guide.md#agent-support) explains instruction files and
skill export. The [MCP server](docs/cli-reference.md#mcp) provides read-only wiki
access, and [bundled skills](docs/cli-reference.md#skills) guide documentation
and analysis workflows.

## Common Workflows

| Task | Example |
|---|---|
| [Search the wiki](docs/cli-reference.md#search) | `llm-wiki search "authentication" --limit 5` |
| [Build agent context](docs/cli-reference.md#context) | `llm-wiki context --budget 8000 --format markdown` |
| [Review changed code](docs/cli-reference.md#review) | `llm-wiki review --base main --head HEAD` |
| [Compare OpenAPI exports](docs/cli-reference.md#api-diff) | `llm-wiki api-diff --baseline api/before.json --candidate api/after.json` |
| [Find documentation work](docs/cli-reference.md#queue) | `llm-wiki queue --limit 30` |
| [Diagnose helper setup and wiki health](docs/cli-reference.md#doctor) | `llm-wiki doctor --capabilities` |

## Automation

Install a read-only GitHub Actions integrity gate after creating your wiki.
The [automation guide](docs/automation.md#install-the-full-integrity-gate)
covers the immutable release reference, permissions, helper preparation, and
advisory PR impact reports. It also covers optional health dashboards and
manual agent triggers.

## Command Reference

The [command reference](docs/cli-reference.md) contains complete workflows,
output formats, exit codes, migration guidance, and resource controls.
Use `llm-wiki <command> --help` for available options.

| Guide | Use it for |
|---|---|
| [Wiki guide](docs/wiki-guide.md) | Page structure, ownership, source selection, and agent setup |
| [Standalone documentation](docs/standalone-documentation.md) | An isolated documentation workspace, agent handoffs, and export |
| [Native knowledge](docs/native-knowledge.md) | Evidence, freshness, durable identity, and read APIs |
| [Qualified context packets](docs/qualified-context-packets.md) | Validated context handoffs and packet contracts |
| [Automation](docs/automation.md) | CI integrity, diagnostics, and explicit triggers |
| [Changelog](CHANGELOG.md) | Release history and compatibility changes |

## Security Model

Built-in extraction reads source without importing the target application.
Project plugins are trusted Python code, and manual agent triggers use the
agent's own permissions. Review generated prompts before sharing sensitive
source. See the [security model](docs/security-model.md) and
[vulnerability reporting policy](SECURITY.md).

## Contribution Policy

This project does not maintain a formal contribution process. You are welcome to
freely fork it, adapt it to your workflow, and publish your own changes under
the [MIT license](LICENSE). Community interactions follow the
[code of conduct](CODE_OF_CONDUCT.md).
