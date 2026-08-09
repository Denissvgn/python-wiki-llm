# MCP Integration

The optional MCP server exposes the canonical wiki and bounded graph/context
queries to local agents. Its tools and resources are read-only; source and wiki
updates remain explicit CLI operations.

## Install and start

Install the optional runtime, then start the default stdio transport from the
source root:

```bash
pip install "agent-wiki-cli[mcp]"
llm-wiki mcp --src-dir . --wiki-dir docs/llm_wiki
```

For a local HTTP client, bind to loopback:

```bash
llm-wiki mcp \
  --transport http \
  --host 127.0.0.1 \
  --port 8765 \
  --src-dir . \
  --wiki-dir docs/llm_wiki
```

HTTP mode rejects non-loopback hosts. Configure allowed origins only for the
local clients that need them.

## Choose the smallest read

- Read canonical pages directly with resources such as
  `llm-wiki://modules/cli` or with `get_module`, `get_entity`, `get_flow`, and
  `get_architecture_page`.
- Use `search_wiki` to locate relevant pages across registered surfaces.
- Use `query_graph` for bounded callers, callees, dependency-neighborhood,
  entry-point flow, data-flow, and symbol-page queries.
- Use `get_context` or `get_context_packet` when an agent needs a token-bounded
  multi-page context rather than a single document.
- Use `check_wiki` for validation and `get_status` for a snapshot-only health
  summary.

Limits default to bounded values and externally supplied limits are capped.
Inspect totals and truncation fields before assuming a collection is complete.

## Keep the server aligned

Start MCP with the same `--source-selection` used to build and sync the wiki.
The service pins that selection for its lifetime and checks it before reads. If
the profile or its controlling files change, stop the server, run sync with the
same profile, and restart it.

The command module loads the optional MCP implementation only when `mcp` is
invoked, keeping ordinary CLI startup independent of the optional SDK. The
[MCP command](../modules/mcp_cmd.md) validates launch options; the
[MCP service](../modules/mcp_server.md) owns page resolution, bounded queries,
resources, and transport safeguards.
