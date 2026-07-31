"""Run llm-wiki as a local Model Context Protocol server."""

from __future__ import annotations

import sys
from typing import Any


_MCP_SERVICE_EXPORTS = frozenset(
    {
        "MCPDependencyError",
        "McpServerConfig",
        "McpWikiError",
        "run_mcp_server",
    }
)
_MISSING = object()


def _mcp_service_export(name: str) -> Any:
    value = globals().get(name, _MISSING)
    if value is not _MISSING:
        return value
    from ..services import mcp_server

    value = getattr(mcp_server, name)
    globals()[name] = value
    return value


def __getattr__(name: str) -> Any:
    """Lazily preserve the command module's historical MCP imports."""

    if name in _MCP_SERVICE_EXPORTS:
        return _mcp_service_export(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def run(args) -> None:
    # The MCP service imports the public API, which includes optional
    # calibration entry points.  Cross that boundary only when MCP is run so
    # base CLI import and parser construction remain calibration-free.
    config_type = _mcp_service_export("McpServerConfig")
    dependency_error = _mcp_service_export("MCPDependencyError")
    wiki_error = _mcp_service_export("McpWikiError")
    runner = _mcp_service_export("run_mcp_server")

    config = config_type(
        src_dir=getattr(args, "src_dir", "."),
        wiki_dir=getattr(args, "wiki_dir", "docs/llm_wiki"),
        transport=getattr(args, "transport", "stdio"),
        host=getattr(args, "host", "127.0.0.1"),
        port=getattr(args, "port", 8765),
        path=getattr(args, "path", "/mcp"),
        allowed_origins=tuple(getattr(args, "allowed_origin", None) or ()),
    )
    try:
        runner(config)
    except (dependency_error, wiki_error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
