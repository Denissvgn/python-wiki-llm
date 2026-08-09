# Troubleshooting and Security

Most failures are deliberate guardrails around source boundaries, helper
availability, managed wiki state, or a requested update that is wider than
expected. Preserve the guardrail, inspect the reported paths, and correct the
input rather than bypassing validation.

## Common recovery paths

### A helper is unavailable

Prepare helper languages explicitly, then point source-reading commands at the
same helper cache when needed:

```bash
export LLM_WIKI_CACHE_DIR=/path/to/llm-wiki-cache
llm-wiki prepare-extractors \
  --cache-dir "$LLM_WIKI_CACHE_DIR" \
  --src-dir .
llm-wiki sync \
  --helper-cache-dir "$LLM_WIKI_CACHE_DIR" \
  --jobs 1 \
  --src-dir . \
  --wiki-dir docs/llm_wiki
```

`prepare-extractors --cache-dir` chooses where helpers are built;
`--helper-cache-dir` tells consuming commands where to find that same root.
Extraction and validation never install a missing toolchain automatically.

### The source selection no longer matches

Use the same profile path for every source-reading operation. After an
intentional profile or `.gitignore` change, preview and sync the wiki before
restarting readers such as MCP:

```bash
llm-wiki sync --dry-run --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
```

### Bootstrap refuses the target

Bootstrap is first-use only. For a managed wiki, use `sync`. For an older or
partial layout, inspect `migrate --dry-run`. The compatibility `--overwrite`
flag does not authorize replacement.

### Sync reports a broad change

Read the dry-run plan and source-selection boundary. Use `--force` only after
confirming that the full set of page additions, updates, retirements, and
architecture changes is intended.

### Strict lint reports stale or broken pages

Run sync first, then inspect the exact reported page and target. Fix semantic
links in guides or supported prose; do not hand-edit generated diagrams,
indexes, or machine-readable sidecars.

## Trust boundaries

- Built-in extractors and prepared helpers statically inspect source and do not
  import the target application.
- Project-local extractor plugins are trusted, unsandboxed Python. Enable them
  only for a source tree you control and have reviewed.
- External source roots require `--allow-external-src`; the wiki destination
  remains subject to the current project boundary.
- Generated prompts can contain source structure and diffs. Review them before
  sharing, and keep credentials and private user data out of source paths and
  documentation.
- MCP tools are read-only. HTTP transport is loopback-only and should use a
  narrow allowed-origin list.
- The canonical wiki is the editable source of truth. Obsidian and site exports
  are derived outputs; make author edits in `docs/llm_wiki` and regenerate the
  projection.

For implementation detail, see [source selection](../modules/source_selection.md),
[source discovery](../modules/source_snapshot.md),
[linting](../modules/lint_service.md), and the
[MCP service](../modules/mcp_server.md).
