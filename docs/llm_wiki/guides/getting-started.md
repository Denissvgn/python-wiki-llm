# Getting Started

LLM Wiki builds a local, navigable description of a repository from static
source analysis. It does not import the target application. Use this guide to
install the command, create the first wiki, and establish the update loop.

## Install

Install the base command from PyPI:

```bash
pip install agent-wiki-cli
```

If you also want the local MCP server, install the optional runtime:

```bash
pip install "agent-wiki-cli[mcp]"
```

## Create the wiki

From the repository root, scaffold agent instructions and then build the first
wiki:

```bash
llm-wiki init --agent generic
llm-wiki bootstrap --src-dir . --wiki-dir docs/llm_wiki
```

`bootstrap` accepts an empty target or the untouched scaffold created by
`init`. Once a managed wiki exists, maintain it with `sync`; bootstrap does not
replace an existing wiki.

## Find your way around

Open [the index](../index.md) first. The main surfaces answer different
questions:

- `guides/` explains supported tasks.
- `modules/` describes source files and their collaborators.
- `entities/` describes classes, records, and declarations.
- `flows/` starts from callable CLI, Python, MCP, and process entry points.
- `workflows/` joins important behavior across modules.
- [Dependencies](../dependencies.md) and [load order](../load-order.md) provide
  architectural views.
- [The log](../log.md) records generated wiki updates.

## Keep it current

Run the update and validation commands from the same source root and with the
same source-selection profile:

```bash
llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
llm-wiki lint --strict --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
```

Review changed semantic sections after sync. The command refreshes generated
structure while preserving supported descriptions, workflow and flow behavior,
architecture notes, and guide prose by default.

## Next steps

- Narrow a repository safely with [source selection](source-selection-and-configuration.md).
- Learn stable command and library entry points in [CLI and Python API](cli-and-python-api.md).
- Expose read-only navigation with [MCP integration](mcp-integration.md).
- Diagnose setup and trust-boundary problems with [troubleshooting and security](troubleshooting-and-security.md).
