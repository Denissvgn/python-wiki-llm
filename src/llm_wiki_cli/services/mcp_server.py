"""Read-only MCP service helpers for exposing an LLM Wiki to agents.

The pure ``McpWikiService`` methods intentionally do not import the optional
MCP SDK.  This keeps the default install dependency-free and gives tests a
stable surface that does not require an MCP runtime.
"""

from __future__ import annotations

import ipaddress
import json
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

from ..api import LlmWikiApiError, build_documentation_query_service
from ..commands import context_cmd, lint_cmd
from ..commands.bootstrap_cmd import build_module_page_map
from ..commands.extract_cmd import get_inventory
from ..config import IDE_AGENTS, get_agent_config_path, read_config, validate_path
from . import circuit_breaker, wiki_surface
from .concept_identity import (
    ConceptIdentityError,
    validate_concept_uid,
    validate_natural_key,
)
from .documentation_queries import DocumentationQueryError
from .io import read_md
from .knowledge_graph import (
    CORE_RELATIONSHIP_KINDS,
    GRAPH_ORIGINS,
    GRAPH_RESOLUTIONS,
)
from .knowledge_observability import (
    knowledge_status_payload,
    load_snapshot_knowledge_observability,
)

MCP_PACKAGE_HINT = "Install it with: pip install 'agent-wiki-cli[mcp]'"
RESOURCE_SCHEME = "llm-wiki"

_PAGE_KINDS_BY_MCP_KIND = {
    entry.mcp_uri_kind: entry for entry in wiki_surface.iter_page_kinds()
}
_MCP_KIND_BY_PAGE_KIND = {
    entry.kind: entry.mcp_uri_kind for entry in wiki_surface.iter_page_kinds()
}
_RESOURCE_KINDS = {entry.mcp_uri_kind for entry in wiki_surface.iter_directory_kinds()}
_ROOT_RESOURCES = {
    entry.mcp_uri_kind: entry for entry in wiki_surface.iter_root_pages()
}
_SEARCH_KINDS = set(_PAGE_KINDS_BY_MCP_KIND)
_ARCHITECTURE_PAGE_KINDS = {"api-contracts", "dependencies", "load-order"}
_MAX_QUERY_LIMIT = 100
_GRAPH_QUERY_METHODS = {
    "flow_for_entrypoint": "flow_for_entrypoint",
    "data_flow_for_entrypoint": "data_flow_for_entrypoint",
    "callers": "callers",
    "callees": "callees",
    "dependency_neighborhood": "dependency_neighborhood",
    "pages_for_symbol": "pages_for_symbol",
}
_KNOWLEDGE_DIRECTIONS = ("inbound", "outbound", "both")
_KNOWLEDGE_RELATIONSHIP_KINDS = ("derived_from", "links_to")
_SECTION_OWNERSHIP_VALUES = ("generated", "semantic", "mixed", "unknown")
_TYPED_GRAPH_DIRECTIONS = ("incoming", "outgoing", "both")
_QUALIFIED_GRAPH_KIND_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9._-]*/[A-Za-z][A-Za-z0-9._-]*$"
)


class MCPDependencyError(RuntimeError):
    """Raised when the optional MCP runtime cannot be used."""


class McpWikiError(ValueError):
    """Raised for invalid MCP wiki requests."""


@dataclass(frozen=True)
class McpServerConfig:
    src_dir: str = "."
    wiki_dir: str = "docs/llm_wiki"
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8765
    path: str = "/mcp"
    allowed_origins: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class WikiPage:
    kind: str
    page_id: str
    path: Path
    uri: str


def ensure_mcp_runtime() -> None:
    """Validate that the optional MCP SDK can be imported on this runtime."""
    if sys.version_info < (3, 10):
        raise MCPDependencyError(
            "llm-wiki MCP support requires Python 3.10 or newer because the "
            "official MCP Python SDK does not support Python 3.9. " + MCP_PACKAGE_HINT
        )
    try:
        import mcp  # type: ignore[reportMissingImports]  # noqa: F401
    except ImportError as exc:
        raise MCPDependencyError(
            "The optional MCP Python SDK is not installed. " + MCP_PACKAGE_HINT
        ) from exc


def validate_loopback_host(host: str) -> None:
    """Reject non-loopback HTTP binds for local-only MCP v1."""
    if _is_loopback_host(host):
        return
    raise McpWikiError(
        "HTTP MCP transport is local-only in v1. Use 127.0.0.1, ::1, or localhost."
    )


def _is_loopback_host(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _default_port_for_scheme(scheme: str) -> int | None:
    if scheme == "http":
        return 80
    if scheme == "https":
        return 443
    return None


def _normalise_origin(origin: str) -> str:
    parsed = urlparse(origin)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise McpWikiError(f"Invalid allowed origin: {origin}")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise McpWikiError(f"Invalid allowed origin: {origin}")
    try:
        port = parsed.port
    except ValueError as exc:
        raise McpWikiError(f"Invalid allowed origin: {origin}") from exc
    host = parsed.hostname.lower()
    host_part = f"[{host}]" if ":" in host else host
    port_part = f":{port}" if port is not None else ""
    return f"{parsed.scheme.lower()}://{host_part}{port_part}"


def is_origin_allowed(
    origin: str, *, port: int, allowed_origins: list[str] | tuple[str, ...]
) -> bool:
    """Return True when an HTTP Origin is acceptable for local MCP use."""
    try:
        normalised = _normalise_origin(origin)
    except McpWikiError:
        return False
    explicit = {_normalise_origin(item) for item in allowed_origins}
    if normalised in explicit:
        return True

    parsed = urlparse(normalised)
    origin_port = (
        parsed.port
        if parsed.port is not None
        else _default_port_for_scheme(parsed.scheme)
    )
    return bool(
        parsed.hostname and _is_loopback_host(parsed.hostname) and origin_port == port
    )


class OriginValidationMiddleware:
    """Minimal ASGI middleware that rejects unexpected browser origins."""

    def __init__(
        self,
        app,
        *,
        port: int,
        allowed_origins: list[str] | tuple[str, ...] | None = None,
    ):
        self.app = app
        self.port = port
        self.allowed_origins = tuple(allowed_origins or ())

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            headers = {key.lower(): value for key, value in scope.get("headers", [])}
            raw_origin = headers.get(b"origin")
            if raw_origin is not None:
                origin = raw_origin.decode("latin1")
                if not is_origin_allowed(
                    origin, port=self.port, allowed_origins=self.allowed_origins
                ):
                    await send(
                        {
                            "type": "http.response.start",
                            "status": 403,
                            "headers": [
                                (b"content-type", b"text/plain; charset=utf-8")
                            ],
                        }
                    )
                    await send(
                        {
                            "type": "http.response.body",
                            "body": b"Forbidden origin",
                        }
                    )
                    return
        await self.app(scope, receive, send)


class McpWikiService:
    """Pure read/check operations exposed through MCP tools and resources."""

    def __init__(self, src_dir: str = ".", wiki_dir: str = "docs/llm_wiki"):
        self.src_dir = src_dir
        self.wiki_dir = Path(wiki_dir)

    def get_entity(self, entity_id: str) -> dict:
        page = self._page_for("entities", entity_id)
        return self._read_page_result(page)

    def get_module(self, module_id_or_source_path: str) -> dict:
        page_id = self._resolve_module_page_id(module_id_or_source_path)
        page = self._page_for("modules", page_id)
        return self._read_page_result(page)

    def get_flow(self, flow_id: str) -> dict:
        page = self._page_for("flows", flow_id)
        return self._read_page_result(page)

    def get_architecture_page(self, page: str) -> dict:
        if not isinstance(page, str) or page.strip() not in _ARCHITECTURE_PAGE_KINDS:
            raise McpWikiError(f"Unknown architecture page: {page}")
        root_page = self._page_from_uri(wiki_surface.mcp_uri(page.strip()))
        return self._read_page_result(root_page)

    def query_graph(self, query: Mapping[str, object]) -> dict:
        query_type, value, limit = _graph_query_args(query)
        try:
            query_service = build_documentation_query_service(
                self.src_dir,
                wiki_dir=str(self.wiki_dir),
                limit=limit,
            )
            method = getattr(query_service, _GRAPH_QUERY_METHODS[query_type])
            return method(value)
        except (LlmWikiApiError, DocumentationQueryError) as exc:
            raise McpWikiError(str(exc)) from exc

    def get_concept(
        self,
        locator_or_exact_route: str,
        limit: int = 20,
    ) -> dict:
        """Return one concept by current coordinate, durable UID, or alias."""
        locator = _knowledge_locator(locator_or_exact_route)
        bounded_limit = _bounded_query_limit(limit)
        return self._run_documentation_query(
            "get_concept",
            locator,
            limit=bounded_limit,
        )

    def related_concepts(
        self,
        locator_or_exact_route: str,
        direction: str = "both",
        kinds: list[str] | None = None,
        limit: int = 20,
    ) -> dict:
        """Return bounded relationships for one exact concept identity."""
        locator = _knowledge_locator(locator_or_exact_route)
        selected_direction = _knowledge_direction(direction)
        selected_kinds = _knowledge_kinds(kinds)
        bounded_limit = _bounded_query_limit(limit)
        return self._run_documentation_query(
            "related_concepts",
            locator,
            limit=bounded_limit,
            direction=selected_direction,
            kinds=selected_kinds,
        )

    def list_concept_sections(
        self,
        locator_or_exact_route: str,
        ownership: str | None = None,
        limit: int = 20,
    ) -> dict:
        """Return bounded document-order sections for one exact concept."""
        locator = _knowledge_locator(locator_or_exact_route)
        selected_ownership = _section_ownership(ownership)
        bounded_limit = _bounded_query_limit(limit)
        return self._run_documentation_query(
            "list_concept_sections",
            locator,
            limit=bounded_limit,
            ownership=selected_ownership,
        )

    def traverse_typed_graph(
        self,
        locator_or_exact_route: str,
        direction: str = "both",
        kinds: list[str] | None = None,
        origins: list[str] | None = None,
        resolutions: list[str] | None = None,
        include_evidence: bool = False,
        limit: int = 20,
    ) -> dict:
        """Traverse bounded persisted typed relationships for one concept."""
        locator = _knowledge_locator(locator_or_exact_route)
        selected_direction = _typed_graph_direction(direction)
        selected_kinds = _typed_graph_kinds(kinds)
        selected_origins = _typed_graph_enum_values(
            origins,
            field="origins",
            allowed=GRAPH_ORIGINS,
        )
        selected_resolutions = _typed_graph_enum_values(
            resolutions,
            field="resolutions",
            allowed=GRAPH_RESOLUTIONS,
        )
        if not isinstance(include_evidence, bool):
            raise McpWikiError("include_evidence must be a boolean.")
        bounded_limit = _bounded_query_limit(limit)
        return self._run_documentation_query(
            "traverse_typed_graph",
            locator,
            limit=bounded_limit,
            direction=selected_direction,
            kinds=selected_kinds,
            origins=selected_origins,
            resolutions=selected_resolutions,
            include_evidence=include_evidence,
        )

    def explain_evidence(
        self,
        locator_or_exact_route: str,
        limit: int = 20,
    ) -> dict:
        """Return bounded evidence for one exact concept identity."""
        locator = _knowledge_locator(locator_or_exact_route)
        bounded_limit = _bounded_query_limit(limit)
        return self._run_documentation_query(
            "explain_evidence",
            locator,
            limit=bounded_limit,
        )

    def search_wiki(
        self,
        query: str,
        kinds: list[str] | None = None,
        limit: int = 20,
    ) -> dict:
        if not isinstance(query, str) or not query.strip():
            raise McpWikiError("query must be a non-empty string.")
        limit = _bounded_query_limit(limit)

        requested = set(kinds or _SEARCH_KINDS)
        unknown = requested - _SEARCH_KINDS
        if unknown:
            raise McpWikiError(f"Unknown wiki search kind: {sorted(unknown)[0]}")

        needle = query.casefold()
        matches: list[dict] = []
        total = 0
        for page in self._iter_pages(requested):
            content = read_md(page.path)
            haystack = content.casefold()
            idx = haystack.find(needle)
            if idx == -1:
                continue
            total += 1
            if len(matches) == limit:
                continue
            matches.append(
                {
                    "kind": page.kind,
                    "id": page.page_id,
                    "uri": page.uri,
                    "path": _relative_posix(page.path, self.wiki_dir),
                    "title": _markdown_title(content, page.page_id),
                    "snippet": _snippet(content, idx, len(query)),
                }
            )

        returned = len(matches)
        bounds = {
            "total": total,
            "returned": returned,
            "truncated": total > returned,
        }
        return {
            "query": query,
            "total": total,
            "returned": returned,
            "count": returned,
            "truncated": bounds["truncated"],
            "bounds": {"results": bounds},
            "results": matches,
        }

    def get_context(
        self,
        budget_tokens: int = 32000,
        focus: list[str] | None = None,
        format: str = "markdown",
        filters: dict | None = None,
    ) -> dict:
        request = {
            "protocol": context_cmd.PROTOCOL_VERSION,
            "budget_tokens": budget_tokens,
            "focus": focus or ["changed", "neighbors"],
            "format": format,
            "filters": filters or {},
        }
        try:
            validated = context_cmd._validate_protocol_request(request)
            payload, warnings = context_cmd._build_context(
                self.src_dir,
                validated["budget_tokens"],
                validated["format"],
                validated["focus"],
                validated["filters"],
                emit_warnings=False,
                wiki_dir=str(self.wiki_dir),
            )
        except context_cmd.ProtocolRequestError as exc:
            raise McpWikiError(str(exc)) from exc
        return context_cmd._protocol_success_payload(validated, payload, warnings)

    def check_wiki(
        self,
        strict: bool = False,
        format: str = "json",
        knowledge_drift_gate: bool = False,
    ) -> dict:
        if format not in {"json", "text", "markdown"}:
            raise McpWikiError("format must be 'json', 'text', or 'markdown'.")
        report = lint_cmd.build_report(
            self.wiki_dir,
            self.src_dir,
            strict=strict,
            knowledge_drift_gate=knowledge_drift_gate,
        )
        payload = lint_cmd.report_to_dict(report)
        _normalise_report_paths(payload)
        if format == "text":
            payload["content"] = lint_cmd.render_text(report)
        elif format == "markdown":
            payload["content"] = lint_cmd.render_markdown(report)
        payload["format"] = format
        return payload

    def get_status(self) -> dict:
        wiki = self.wiki_dir
        pages = {
            entry.mcp_uri_kind: _count_surface_pages(wiki, entry)
            for entry in wiki_surface.iter_page_kinds()
        }
        pages["architecture_pages"] = sum(
            pages[kind] for kind in _ARCHITECTURE_PAGE_KINDS
        )
        knowledge_observability = load_snapshot_knowledge_observability(
            wiki,
            src_dir=self.src_dir,
        )
        knowledge_status = knowledge_status_payload(knowledge_observability.view)
        status: dict[str, object] = {
            "wiki_dir": _posix_string(wiki),
            "wiki_exists": wiki.exists(),
            "pages": pages,
            "knowledge": knowledge_status,
        }
        if knowledge_status["availability"] != "absent":
            status["knowledge_summary"] = knowledge_observability.summary.to_payload()

        agent_config = get_agent_config_path(wiki)
        if agent_config.exists():
            try:
                config = read_config(wiki)
                agent = str(config.get("agent", "unknown"))
                status["agent"] = {
                    "configured": True,
                    "name": agent,
                    "mode": "IDE" if agent in IDE_AGENTS else "CLI",
                    "quality_hints": bool(config.get("quality_hints", True)),
                    "issue_reporting": bool(config.get("issue_reporting", False)),
                }
            except Exception as exc:
                status["agent"] = {"configured": False, "error": str(exc)}
        else:
            status["agent"] = {"configured": False}

        status["hooks"] = _installed_hooks()
        state = (
            circuit_breaker.load_state(Path(".git")) if Path(".git").exists() else {}
        )
        status["circuit_breaker"] = {
            "state": state.get(
                "state", "unavailable" if not Path(".git").exists() else "closed"
            ),
            "consecutive_failures": state.get("consecutive_failures", 0),
        }
        return status

    def _run_documentation_query(
        self,
        method_name: str,
        value: str,
        *,
        limit: int,
        **query_options,
    ) -> dict:
        try:
            query_service = build_documentation_query_service(
                self.src_dir,
                wiki_dir=str(self.wiki_dir),
                limit=limit,
                read_only=True,
            )
            method = getattr(query_service, method_name)
            return method(value, **query_options)
        except (LlmWikiApiError, DocumentationQueryError) as exc:
            raise McpWikiError(str(exc)) from exc

    def read_resource(self, uri: str) -> dict:
        page = self._page_from_uri(uri)
        result = self._read_page_result(page)
        return {
            "uri": page.uri,
            "mimeType": "text/markdown",
            "text": result["content"],
            "metadata": {
                "kind": page.kind,
                "id": page.page_id,
                "path": result["path"],
                "title": result["title"],
            },
        }

    def list_resources(self) -> list[dict]:
        resources = []
        for page in self._iter_pages(_SEARCH_KINDS):
            resources.append(
                {
                    "uri": page.uri,
                    "name": f"{page.kind}/{page.page_id}"
                    if page.kind not in _ROOT_RESOURCES
                    else page.page_id,
                    "title": page.page_id,
                    "mimeType": "text/markdown",
                }
            )
        return resources

    def _resolve_module_page_id(self, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise McpWikiError("module_id_or_source_path must be a non-empty string.")
        candidate = value.strip()
        if (
            _is_safe_page_id(candidate)
            and (self.wiki_dir / "modules" / f"{candidate}.md").exists()
        ):
            return candidate

        inventory = get_inventory(self.src_dir)
        page_map = build_module_page_map(inventory)
        normalised = _normalise_source_path(candidate)
        if normalised in page_map:
            return page_map[normalised]

        suffix_matches = [
            page_id
            for filepath, page_id in page_map.items()
            if filepath.endswith(normalised) or normalised.endswith(filepath)
        ]
        if len(suffix_matches) == 1:
            return suffix_matches[0]
        if len(suffix_matches) > 1:
            raise McpWikiError(f"Ambiguous module source path: {value}")

        if _is_safe_page_id(candidate):
            return candidate
        raise McpWikiError(f"Unknown module source path or unsafe page id: {value}")

    def _page_for(self, kind: str, page_id: str) -> WikiPage:
        entry = _PAGE_KINDS_BY_MCP_KIND.get(kind)
        if entry is None or not entry.requires_page_id:
            raise McpWikiError(f"Unknown wiki resource kind: {kind}")
        page_id = _validate_page_id(page_id)
        path = self.wiki_dir / wiki_surface.canonical_path(entry.kind, page_id)
        _ensure_inside(self.wiki_dir, path)
        if not path.exists():
            raise McpWikiError(
                f"Wiki page not found: {wiki_surface.canonical_path(entry.kind, page_id)}"
            )
        return WikiPage(
            kind=entry.mcp_uri_kind,
            page_id=page_id,
            path=path,
            uri=_resource_uri(entry.mcp_uri_kind, page_id),
        )

    def _page_from_uri(self, uri: str) -> WikiPage:
        parsed = urlparse(uri)
        if parsed.scheme != RESOURCE_SCHEME:
            raise McpWikiError(f"Unsupported resource URI scheme: {parsed.scheme}")
        if parsed.netloc in _ROOT_RESOURCES and parsed.path in {"", "/"}:
            entry = _ROOT_RESOURCES[parsed.netloc]
            page_id = entry.mcp_uri_kind
            path = self.wiki_dir / wiki_surface.canonical_path(entry.kind)
            _ensure_inside(self.wiki_dir, path)
            if not path.exists():
                raise McpWikiError(
                    f"Wiki page not found: {wiki_surface.canonical_path(entry.kind)}"
                )
            return WikiPage(
                kind=entry.mcp_uri_kind,
                page_id=page_id,
                path=path,
                uri=wiki_surface.mcp_uri(entry.kind),
            )

        kind = parsed.netloc
        raw_id = parsed.path.lstrip("/")
        if "/" in raw_id:
            raise McpWikiError(f"Invalid wiki resource URI: {uri}")
        return self._page_for(kind, unquote(raw_id))

    def _read_page_result(self, page: WikiPage) -> dict:
        content = read_md(page.path)
        return {
            "kind": page.kind,
            "id": page.page_id,
            "uri": page.uri,
            "path": _relative_posix(page.path, self.wiki_dir),
            "title": _markdown_title(content, page.page_id),
            "content": content,
        }

    def _iter_pages(self, kinds: set[str]):
        for page in wiki_surface.collect_wiki_pages(self.wiki_dir):
            kind = _MCP_KIND_BY_PAGE_KIND[page.kind]
            if kind in kinds:
                yield WikiPage(kind, page.page_id, page.path, page.mcp_uri)


def create_mcp_server(config: McpServerConfig):
    """Create and register the FastMCP server for a validated config."""
    ensure_mcp_runtime()
    from mcp.server.fastmcp import FastMCP  # type: ignore[reportMissingImports]

    service = McpWikiService(src_dir=config.src_dir, wiki_dir=config.wiki_dir)
    server = FastMCP(
        "llm-wiki",
        instructions=(
            "Read-only access to the local LLM Wiki. Use tools to fetch wiki pages, "
            "search documentation, query documentation and knowledge graphs, "
            "request generated context, and run checks."
        ),
    )

    _register_mcp_tools(server, service)
    _register_mcp_resources(server, service)

    return server


def _register_mcp_tools(server, service: McpWikiService) -> None:
    @server.tool()
    def get_entity(entity_id: str) -> dict:
        """Return a wiki entity page by entity page id."""
        return service.get_entity(entity_id)

    @server.tool()
    def get_module(module_id_or_source_path: str) -> dict:
        """Return a wiki module page by page id or source path."""
        return service.get_module(module_id_or_source_path)

    @server.tool()
    def get_flow(flow_id: str) -> dict:
        """Return a wiki user-flow page by flow page id."""
        return service.get_flow(flow_id)

    @server.tool()
    def get_architecture_page(page: str) -> dict:
        """Return a wiki dependency architecture page."""
        return service.get_architecture_page(page)

    @server.tool()
    def query_graph(query: dict) -> dict:
        """Run a bounded read-only documentation graph query."""
        return service.query_graph(query)

    @server.tool()
    def get_concept(
        locator_or_exact_route: str,
        limit: int = 20,
    ) -> dict:
        """Return one concept by current coordinate, durable UID, or alias."""
        return service.get_concept(locator_or_exact_route, limit=limit)

    @server.tool()
    def related_concepts(
        locator_or_exact_route: str,
        direction: str = "both",
        kinds: list[str] | None = None,
        limit: int = 20,
    ) -> dict:
        """Return bounded relationships for one exact concept identity."""
        return service.related_concepts(
            locator_or_exact_route,
            direction=direction,
            kinds=kinds,
            limit=limit,
        )

    @server.tool()
    def list_concept_sections(
        locator_or_exact_route: str,
        ownership: str | None = None,
        limit: int = 20,
    ) -> dict:
        """Return bounded document-order sections for one exact concept."""
        return service.list_concept_sections(
            locator_or_exact_route,
            ownership=ownership,
            limit=limit,
        )

    @server.tool()
    def traverse_typed_graph(
        locator_or_exact_route: str,
        direction: str = "both",
        kinds: list[str] | None = None,
        origins: list[str] | None = None,
        resolutions: list[str] | None = None,
        include_evidence: bool = False,
        limit: int = 20,
    ) -> dict:
        """Traverse bounded persisted typed relationships for one concept."""
        return service.traverse_typed_graph(
            locator_or_exact_route,
            direction=direction,
            kinds=kinds,
            origins=origins,
            resolutions=resolutions,
            include_evidence=include_evidence,
            limit=limit,
        )

    @server.tool()
    def explain_evidence(
        locator_or_exact_route: str,
        limit: int = 20,
    ) -> dict:
        """Return bounded evidence for one exact concept identity."""
        return service.explain_evidence(locator_or_exact_route, limit=limit)

    @server.tool()
    def search_wiki(
        query: str, kinds: list[str] | None = None, limit: int = 20
    ) -> dict:
        """Search Markdown wiki pages and return snippets plus resource URIs."""
        return service.search_wiki(query, kinds=kinds, limit=limit)

    @server.tool()
    def get_context(
        budget_tokens: int = 32000,
        focus: list[str] | None = None,
        format: str = "markdown",
        filters: dict | None = None,
    ) -> dict:
        """Return priority-ranked codebase context from llm-wiki context."""
        return service.get_context(
            budget_tokens=budget_tokens,
            focus=focus,
            format=format,
            filters=filters,
        )

    @server.tool()
    def check_wiki(
        strict: bool = False,
        format: str = "json",
        knowledge_drift_gate: bool = False,
    ) -> dict:
        """Run read-only wiki lint checks and return a structured report."""
        return service.check_wiki(
            strict=strict,
            format=format,
            knowledge_drift_gate=knowledge_drift_gate,
        )

    @server.tool()
    def get_status() -> dict:
        """Return local llm-wiki status without mutating files."""
        return service.get_status()


def _register_mcp_resources(server, service: McpWikiService) -> None:
    for entry in wiki_surface.iter_page_kinds():
        if entry.requires_page_id:
            _register_directory_resource(server, service, entry)
        else:
            _register_root_resource(server, service, entry)


def _register_root_resource(server, service: McpWikiService, entry) -> None:
    uri = wiki_surface.mcp_uri(entry.kind)

    def resource() -> str:
        return service.read_resource(uri)["text"]

    resource.__name__ = f"{entry.mcp_uri_kind.replace('-', '_')}_resource"
    resource.__doc__ = f"Read the wiki {entry.label.lower()} page."
    server.resource(uri)(resource)


def _register_directory_resource(server, service: McpWikiService, entry) -> None:
    template = f"{RESOURCE_SCHEME}://{entry.mcp_uri_kind}/{{page_id}}"

    def resource(page_id: str) -> str:
        uri = wiki_surface.mcp_uri(entry.kind, page_id)
        return service.read_resource(uri)["text"]

    resource.__name__ = f"{entry.mcp_uri_kind.replace('-', '_')}_resource"
    resource.__doc__ = f"Read a wiki {entry.label.lower()} resource."
    server.resource(template)(resource)


def run_mcp_server(config: McpServerConfig) -> None:
    """Validate, build, and run the MCP server."""
    validate_path(config.src_dir, "--src-dir")
    validate_path(config.wiki_dir, "--wiki-dir")
    if config.transport not in {"stdio", "http"}:
        raise McpWikiError("transport must be 'stdio' or 'http'.")
    if config.transport == "http":
        validate_loopback_host(config.host)
        if config.port < 1 or config.port > 65535:
            raise McpWikiError("HTTP port must be between 1 and 65535.")
        if not config.path.startswith("/"):
            raise McpWikiError("HTTP MCP endpoint path must start with '/'.")
        for origin in config.allowed_origins:
            _normalise_origin(origin)

    server = create_mcp_server(config)

    if config.transport == "stdio":
        server.run(transport="stdio", show_banner=False)
        return

    from starlette.middleware import Middleware  # type: ignore[reportMissingImports]

    middleware = [
        Middleware(
            OriginValidationMiddleware,
            port=config.port,
            allowed_origins=list(config.allowed_origins),
        )
    ]
    server.run(
        transport="streamable-http",
        show_banner=False,
        host=config.host,
        port=config.port,
        path=config.path,
        middleware=middleware,
    )


def _resource_uri(kind: str, page_id: str) -> str:
    return wiki_surface.mcp_uri(kind, page_id)


def _graph_query_args(query: Mapping[str, object]) -> tuple[str, str, int]:
    if not isinstance(query, Mapping):
        raise McpWikiError("query must be an object.")

    unknown = sorted(set(query) - {"type", "value", "limit"})
    if unknown:
        raise McpWikiError(f"Unknown query field: {unknown[0]}")

    query_type = query.get("type")
    if not isinstance(query_type, str) or not query_type.strip():
        raise McpWikiError("type must be a non-empty string.")
    query_type = query_type.strip()
    if query_type not in _GRAPH_QUERY_METHODS:
        raise McpWikiError(f"Unknown graph query type: {query_type}")

    value = query.get("value")
    if not isinstance(value, str) or not value.strip():
        raise McpWikiError("value must be a non-empty string.")

    limit = _bounded_query_limit(query.get("limit", 20))

    return query_type, value.strip(), limit


def _knowledge_locator(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise McpWikiError(
            "locator_or_exact_route must be a non-empty string."
        )
    selected = value.strip()
    try:
        return wiki_surface.validate_exact_page_coordinate(selected)
    except wiki_surface.WikiSurfaceError:
        pass
    for validator in (validate_concept_uid, validate_natural_key):
        try:
            return validator(selected)
        except ConceptIdentityError:
            continue
    raise McpWikiError(
        "locator_or_exact_route must be an exact canonical wiki path or "
        "llm-wiki URI, durable concept UID, or natural-key alias."
    )


def _knowledge_direction(value: object) -> str:
    if not isinstance(value, str) or value not in _KNOWLEDGE_DIRECTIONS:
        choices = ", ".join(repr(item) for item in _KNOWLEDGE_DIRECTIONS)
        raise McpWikiError(f"direction must be one of {choices}.")
    return value


def _section_ownership(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value not in _SECTION_OWNERSHIP_VALUES:
        choices = ", ".join(repr(item) for item in _SECTION_OWNERSHIP_VALUES)
        raise McpWikiError(f"ownership must be one of {choices}, or None.")
    return value


def _knowledge_kinds(values: object) -> list[str] | None:
    if values is None:
        return None
    if isinstance(values, (str, bytes, Mapping)):
        raise McpWikiError(
            "kinds must be an iterable of relationship kind strings."
        )
    if not isinstance(values, Iterable):
        raise McpWikiError(
            "kinds must be an iterable of relationship kind strings."
        )
    requested = list(values)
    if any(not isinstance(value, str) for value in requested):
        raise McpWikiError(
            "kinds must contain only relationship kind strings."
        )
    unsupported = sorted(
        set(requested) - set(_KNOWLEDGE_RELATIONSHIP_KINDS)
    )
    if unsupported:
        raise McpWikiError(
            f"unsupported relationship kind: {unsupported[0]!r}."
        )
    selected = set(requested)
    return [
        kind for kind in _KNOWLEDGE_RELATIONSHIP_KINDS if kind in selected
    ]


def _typed_graph_direction(value: object) -> str:
    if not isinstance(value, str) or value not in _TYPED_GRAPH_DIRECTIONS:
        choices = ", ".join(repr(item) for item in _TYPED_GRAPH_DIRECTIONS)
        raise McpWikiError(f"direction must be one of {choices}.")
    return value


def _typed_graph_kinds(values: object) -> list[str] | None:
    if values is None:
        return None
    if isinstance(values, (str, bytes, Mapping)) or not isinstance(
        values, Iterable
    ):
        raise McpWikiError(
            "kinds must be an iterable of typed relationship kind strings."
        )
    requested = list(values)
    if any(not isinstance(value, str) for value in requested):
        raise McpWikiError(
            "kinds must contain only typed relationship kind strings."
        )
    invalid = sorted(
        {
            value
            for value in requested
            if value not in CORE_RELATIONSHIP_KINDS
            and not _QUALIFIED_GRAPH_KIND_RE.fullmatch(value)
        }
    )
    if invalid:
        raise McpWikiError(
            f"unsupported typed relationship kind: {invalid[0]!r}."
        )
    selected = set(requested)
    return [
        *[kind for kind in CORE_RELATIONSHIP_KINDS if kind in selected],
        *sorted(selected - set(CORE_RELATIONSHIP_KINDS)),
    ]


def _typed_graph_enum_values(
    values: object,
    *,
    field: str,
    allowed: tuple[str, ...],
) -> list[str] | None:
    if values is None:
        return None
    if isinstance(values, (str, bytes, Mapping)) or not isinstance(
        values, Iterable
    ):
        raise McpWikiError(f"{field} must be an iterable of strings.")
    requested = list(values)
    if any(not isinstance(value, str) for value in requested):
        raise McpWikiError(f"{field} must contain only strings.")
    unsupported = sorted(set(requested) - set(allowed))
    if unsupported:
        raise McpWikiError(
            f"unsupported {field[:-1]}: {unsupported[0]!r}."
        )
    selected = set(requested)
    return [value for value in allowed if value in selected]


def _bounded_query_limit(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise McpWikiError("limit must be a positive integer.")
    return min(value, _MAX_QUERY_LIMIT)


def _validate_page_id(page_id: str) -> str:
    if not isinstance(page_id, str) or not page_id:
        raise McpWikiError("page id must be a non-empty string.")
    page_id = unquote(page_id)
    if not _is_safe_page_id(page_id):
        raise McpWikiError(f"Unsafe wiki page id: {page_id}")
    return page_id


def _is_safe_page_id(page_id: str) -> bool:
    return wiki_surface.is_safe_page_id(page_id)


def _normalise_source_path(path: str) -> str:
    posix = PurePosixPath(path.replace("\\", "/"))
    if posix.is_absolute() or ".." in posix.parts:
        raise McpWikiError(f"Unsafe source path: {path}")
    return posix.as_posix().lstrip("./")


def _ensure_inside(root: Path, path: Path) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise McpWikiError(f"Wiki path escapes wiki directory: {path}") from exc


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.resolve().relative_to(root.resolve()).as_posix()


def _posix_string(value: object) -> str:
    return str(value).replace("\\", "/")


def _normalise_report_paths(payload: dict) -> None:
    for key in ("wiki_dir", "src_dir"):
        if key in payload:
            payload[key] = _posix_string(payload[key])
    for issue in payload.get("issues", []):
        if isinstance(issue, dict) and issue.get("path") is not None:
            issue["path"] = _posix_string(issue["path"])


def _markdown_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def _snippet(content: str, start: int, length: int) -> str:
    left = max(0, start - 80)
    right = min(len(content), start + length + 80)
    snippet = content[left:right].replace("\n", " ")
    return " ".join(snippet.split())


def _count_md(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.glob("*.md"))


def _count_surface_pages(path: Path, entry) -> int:
    if entry.requires_page_id:
        return _count_md(path / entry.directory)
    return int((path / wiki_surface.canonical_path(entry.kind)).is_file())


def _installed_hooks() -> list[str]:
    hooks_dir = Path(".git") / "hooks"
    if not hooks_dir.exists():
        return []
    installed: list[str] = []
    for hook_name in ["post-commit", "pre-commit", "pre-push"]:
        hook_file = hooks_dir / hook_name
        if not hook_file.exists():
            continue
        try:
            if "LLM Wiki" in hook_file.read_text(encoding="utf-8"):
                installed.append(hook_name)
        except OSError:
            continue
    return installed


def to_json(data: object) -> str:
    """Stable JSON helper for tests and debugging."""
    return json.dumps(data, indent=2, sort_keys=True)
