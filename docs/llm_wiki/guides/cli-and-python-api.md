# CLI and Python API

The command-line interface is the primary operator surface. The supported
Python API exposes the same extraction, bootstrap, context, health, and graph
operations without depending on parser or command-module details.

## Common command loop

Create a first wiki, update it after source changes, and validate it:

```bash
llm-wiki bootstrap --src-dir . --wiki-dir docs/llm_wiki
llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
llm-wiki lint --strict --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
```

Use `extract` when you need the source inventory rather than Markdown:

```bash
llm-wiki extract --src-dir . --summary
llm-wiki extract --src-dir . --deep
```

Use `sync --dry-run` before a broad update. `ci-check` always applies strict
validation, writes a Markdown report, and exits nonzero when blocking issues
remain:

```bash
llm-wiki ci-check --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
```

The [CLI dispatcher](../modules/cli.md) owns argument parsing and routes each
subcommand to its command or service module. Flow pages such as
[bootstrap](../flows/cli-bootstrap.md), [sync](../flows/cli-sync.md), and
[lint](../flows/cli-lint.md) show the generated call boundaries.

## Supported library calls

Import public functions from `llm_wiki_cli.api`:

```python
from llm_wiki_cli import api

inventory = api.extract_source(".", summary=True)
pages = api.list_wiki_pages("docs/llm_wiki")
context = api.build_context(
    ".",
    wiki_dir="docs/llm_wiki",
    focus=["changed", "neighbors"],
    budget=8000,
)
health = api.doctor(".", wiki_dir="docs/llm_wiki", strict=True)
```

For first-use generation, `api.bootstrap_wiki(source_root, wiki_root)` returns
a typed `BootstrapResult`. It always uses source-adapter behavior, so the
library call writes within the wiki target and does not install agent
instructions in the source project.

## Errors and output contracts

Library boundaries normalize failures under `LlmWikiApiError` subclasses.
Invalid arguments, path-policy violations, workspace state, and artifact
integrity remain distinct categories so callers can report or recover without
parsing console text. Structured command modes and typed API results should be
preferred over scraping human-readable output.

The API and MCP graph queries are bounded. Collection results report the total,
returned count, and truncation state; callers should not interpret a bounded
response as a complete repository census.

See the [API module](../modules/api.md),
[bootstrap_wiki flow](../flows/api-bootstrap_wiki.md), and
[extract_source flow](../flows/api-extract_source.md) for the current supported
surface.
