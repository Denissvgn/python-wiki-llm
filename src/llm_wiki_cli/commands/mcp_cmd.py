"""Run llm-wiki as a local Model Context Protocol server."""

from __future__ import annotations

import sys

from ..services.mcp_server import (
    MCPDependencyError,
    McpServerConfig,
    McpWikiError,
    run_mcp_server,
)


def run(args) -> None:
    config = McpServerConfig(
        src_dir=getattr(args, "src_dir", "."),
        wiki_dir=getattr(args, "wiki_dir", "docs/llm_wiki"),
        transport=getattr(args, "transport", "stdio"),
        host=getattr(args, "host", "127.0.0.1"),
        port=getattr(args, "port", 8765),
        path=getattr(args, "path", "/mcp"),
        allowed_origins=tuple(getattr(args, "allowed_origin", None) or ()),
    )
    try:
        run_mcp_server(config)
    except (MCPDependencyError, McpWikiError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
