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
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlparse

from ..config import IDE_AGENTS, get_agent_config_path, read_config, validate_path
from ..commands import context_cmd, lint_cmd
from ..commands.bootstrap_cmd import build_module_page_map
from ..commands.extract_cmd import get_inventory
from . import circuit_breaker
from .io import read_md


MCP_PACKAGE_HINT = "Install it with: pip install 'agent-wiki-cli[mcp]'"
RESOURCE_SCHEME = "llm-wiki"

_PAGE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_RESOURCE_KINDS = {"entities", "modules", "workflows", "infrastructure"}
_ROOT_RESOURCES = {"index": "index.md", "log": "log.md"}
_SEARCH_KINDS = _RESOURCE_KINDS | set(_ROOT_RESOURCES)


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
            "official MCP Python SDK does not support Python 3.9. "
            + MCP_PACKAGE_HINT
        )
    try:
        import mcp  # noqa: F401
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


def is_origin_allowed(origin: str, *, port: int, allowed_origins: list[str] | tuple[str, ...]) -> bool:
    """Return True when an HTTP Origin is acceptable for local MCP use."""
    try:
        normalised = _normalise_origin(origin)
    except McpWikiError:
        return False
    explicit = {_normalise_origin(item) for item in allowed_origins}
    if normalised in explicit:
        return True

    parsed = urlparse(normalised)
    origin_port = parsed.port if parsed.port is not None else _default_port_for_scheme(parsed.scheme)
    return bool(parsed.hostname and _is_loopback_host(parsed.hostname) and origin_port == port)


class OriginValidationMiddleware:
    """Minimal ASGI middleware that rejects unexpected browser origins."""

    def __init__(self, app, *, port: int, allowed_origins: list[str] | tuple[str, ...] | None = None):
        self.app = app
        self.port = port
        self.allowed_origins = tuple(allowed_origins or ())

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            headers = {
                key.lower(): value
                for key, value in scope.get("headers", [])
            }
            raw_origin = headers.get(b"origin")
            if raw_origin is not None:
                origin = raw_origin.decode("latin1")
                if not is_origin_allowed(origin, port=self.port, allowed_origins=self.allowed_origins):
                    await send({
                        "type": "http.response.start",
                        "status": 403,
                        "headers": [(b"content-type", b"text/plain; charset=utf-8")],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": b"Forbidden origin",
                    })
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

    def search_wiki(
        self,
        query: str,
        kinds: list[str] | None = None,
        limit: int = 20,
    ) -> dict:
        if not isinstance(query, str) or not query.strip():
            raise McpWikiError("query must be a non-empty string.")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise McpWikiError("limit must be a positive integer.")
        limit = min(limit, 100)

        requested = set(kinds or _SEARCH_KINDS)
        unknown = requested - _SEARCH_KINDS
        if unknown:
            raise McpWikiError(f"Unknown wiki search kind: {sorted(unknown)[0]}")

        needle = query.casefold()
        matches: list[dict] = []
        for page in self._iter_pages(requested):
            content = read_md(page.path)
            haystack = content.casefold()
            idx = haystack.find(needle)
            if idx == -1:
                continue
            matches.append({
                "kind": page.kind,
                "id": page.page_id,
                "uri": page.uri,
                "path": _relative_posix(page.path, self.wiki_dir),
                "title": _markdown_title(content, page.page_id),
                "snippet": _snippet(content, idx, len(query)),
            })
            if len(matches) >= limit:
                break

        return {"query": query, "count": len(matches), "results": matches}

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
            )
        except context_cmd.ProtocolRequestError as exc:
            raise McpWikiError(str(exc)) from exc
        return context_cmd._protocol_success_payload(validated, payload, warnings)

    def check_wiki(self, strict: bool = False, format: str = "json") -> dict:
        if format not in {"json", "text", "markdown"}:
            raise McpWikiError("format must be 'json', 'text', or 'markdown'.")
        report = lint_cmd.build_report(self.wiki_dir, self.src_dir, strict=strict)
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
        status: dict[str, object] = {
            "wiki_dir": _posix_string(wiki),
            "wiki_exists": wiki.exists(),
            "pages": {
                "entities": _count_md(wiki / "entities"),
                "modules": _count_md(wiki / "modules"),
                "workflows": _count_md(wiki / "workflows"),
                "infrastructure": _count_md(wiki / "infrastructure"),
            },
        }

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
                }
            except Exception as exc:
                status["agent"] = {"configured": False, "error": str(exc)}
        else:
            status["agent"] = {"configured": False}

        status["hooks"] = _installed_hooks()
        state = circuit_breaker.load_state(Path(".git")) if Path(".git").exists() else {}
        status["circuit_breaker"] = {
            "state": state.get("state", "unavailable" if not Path(".git").exists() else "closed"),
            "consecutive_failures": state.get("consecutive_failures", 0),
        }
        return status

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
            resources.append({
                "uri": page.uri,
                "name": f"{page.kind}/{page.page_id}" if page.kind not in _ROOT_RESOURCES else page.page_id,
                "title": page.page_id,
                "mimeType": "text/markdown",
            })
        return resources

    def _resolve_module_page_id(self, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise McpWikiError("module_id_or_source_path must be a non-empty string.")
        candidate = value.strip()
        if _is_safe_page_id(candidate) and (self.wiki_dir / "modules" / f"{candidate}.md").exists():
            return candidate

        inventory = get_inventory(self.src_dir)
        page_map = build_module_page_map(inventory)
        normalised = _normalise_source_path(candidate)
        if normalised in page_map:
            return page_map[normalised]

        suffix_matches = [
            page_id for filepath, page_id in page_map.items()
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
        if kind not in _RESOURCE_KINDS:
            raise McpWikiError(f"Unknown wiki resource kind: {kind}")
        page_id = _validate_page_id(page_id)
        path = self.wiki_dir / kind / f"{page_id}.md"
        _ensure_inside(self.wiki_dir, path)
        if not path.exists():
            raise McpWikiError(f"Wiki page not found: {kind}/{page_id}.md")
        return WikiPage(kind=kind, page_id=page_id, path=path, uri=_resource_uri(kind, page_id))

    def _page_from_uri(self, uri: str) -> WikiPage:
        parsed = urlparse(uri)
        if parsed.scheme != RESOURCE_SCHEME:
            raise McpWikiError(f"Unsupported resource URI scheme: {parsed.scheme}")
        if parsed.netloc in _ROOT_RESOURCES and parsed.path in {"", "/"}:
            page_id = parsed.netloc
            path = self.wiki_dir / _ROOT_RESOURCES[page_id]
            _ensure_inside(self.wiki_dir, path)
            if not path.exists():
                raise McpWikiError(f"Wiki page not found: {_ROOT_RESOURCES[page_id]}")
            return WikiPage(kind=page_id, page_id=page_id, path=path, uri=f"{RESOURCE_SCHEME}://{page_id}")

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
        if "index" in kinds:
            path = self.wiki_dir / "index.md"
            if path.exists():
                yield WikiPage("index", "index", path, f"{RESOURCE_SCHEME}://index")
        if "log" in kinds:
            path = self.wiki_dir / "log.md"
            if path.exists():
                yield WikiPage("log", "log", path, f"{RESOURCE_SCHEME}://log")
        for kind in sorted(_RESOURCE_KINDS & kinds):
            base = self.wiki_dir / kind
            if not base.exists():
                continue
            for path in sorted(base.glob("*.md")):
                if _is_legacy_page(path, self.wiki_dir):
                    continue
                page_id = path.stem
                if _is_safe_page_id(page_id):
                    yield WikiPage(kind, page_id, path, _resource_uri(kind, page_id))


def create_mcp_server(config: McpServerConfig):
    """Create and register the FastMCP server for a validated config."""
    ensure_mcp_runtime()
    from mcp.server.fastmcp import FastMCP

    service = McpWikiService(src_dir=config.src_dir, wiki_dir=config.wiki_dir)
    server = FastMCP(
        "llm-wiki",
        instructions=(
            "Read-only access to the local LLM Wiki. Use tools to fetch wiki pages, "
            "search documentation, request generated context, and run checks."
        ),
    )

    @server.tool()
    def get_entity(entity_id: str) -> dict:
        """Return a wiki entity page by entity page id."""
        return service.get_entity(entity_id)

    @server.tool()
    def get_module(module_id_or_source_path: str) -> dict:
        """Return a wiki module page by page id or source path."""
        return service.get_module(module_id_or_source_path)

    @server.tool()
    def search_wiki(query: str, kinds: list[str] | None = None, limit: int = 20) -> dict:
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
    def check_wiki(strict: bool = False, format: str = "json") -> dict:
        """Run read-only wiki lint checks and return a structured report."""
        return service.check_wiki(strict=strict, format=format)

    @server.tool()
    def get_status() -> dict:
        """Return local llm-wiki status without mutating files."""
        return service.get_status()

    @server.resource("llm-wiki://index")
    def index_resource() -> str:
        """Read the wiki index."""
        return service.read_resource("llm-wiki://index")["text"]

    @server.resource("llm-wiki://log")
    def log_resource() -> str:
        """Read the architectural log."""
        return service.read_resource("llm-wiki://log")["text"]

    @server.resource("llm-wiki://entities/{entity_id}")
    def entity_resource(entity_id: str) -> str:
        """Read a wiki entity resource."""
        return service.read_resource(f"llm-wiki://entities/{quote(entity_id, safe='._-')}")["text"]

    @server.resource("llm-wiki://modules/{module_id}")
    def module_resource(module_id: str) -> str:
        """Read a wiki module resource."""
        return service.read_resource(f"llm-wiki://modules/{quote(module_id, safe='._-')}")["text"]

    @server.resource("llm-wiki://workflows/{workflow_id}")
    def workflow_resource(workflow_id: str) -> str:
        """Read a wiki workflow resource."""
        return service.read_resource(f"llm-wiki://workflows/{quote(workflow_id, safe='._-')}")["text"]

    @server.resource("llm-wiki://infrastructure/{infra_id}")
    def infrastructure_resource(infra_id: str) -> str:
        """Read a wiki infrastructure resource."""
        return service.read_resource(f"llm-wiki://infrastructure/{quote(infra_id, safe='._-')}")["text"]

    return server


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

    from starlette.middleware import Middleware

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
    return f"{RESOURCE_SCHEME}://{kind}/{quote(page_id, safe='._-')}"


def _validate_page_id(page_id: str) -> str:
    if not isinstance(page_id, str) or not page_id:
        raise McpWikiError("page id must be a non-empty string.")
    page_id = unquote(page_id)
    if not _is_safe_page_id(page_id):
        raise McpWikiError(f"Unsafe wiki page id: {page_id}")
    return page_id


def _is_safe_page_id(page_id: str) -> bool:
    return bool(_PAGE_ID_RE.fullmatch(page_id)) and ".." not in page_id


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
    return path.relative_to(root).as_posix()


def _posix_string(value: object) -> str:
    return str(value).replace("\\", "/")


def _normalise_report_paths(payload: dict) -> None:
    for key in ("wiki_dir", "src_dir"):
        if key in payload:
            payload[key] = _posix_string(payload[key])
    for issue in payload.get("issues", []):
        if isinstance(issue, dict) and issue.get("path") is not None:
            issue["path"] = _posix_string(issue["path"])


def _is_legacy_page(path: Path, wiki_dir: Path) -> bool:
    try:
        return path.relative_to(wiki_dir).parts[:1] == ("legacy",)
    except ValueError:
        try:
            return path.resolve().relative_to(wiki_dir.resolve()).parts[:1] == ("legacy",)
        except ValueError:
            return False


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
    return len(list(path.glob("*.md")))


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
