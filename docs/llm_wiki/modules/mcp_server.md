# mcp_server Module

**Path:** `src/llm_wiki_cli/services/mcp_server.py`

## Description

Exposes canonical wiki resources plus bounded search, graph, context, health,
and concept queries through a read-only service. `McpWikiService` resolves
pages and enforces the live source-selection pin without importing the optional
SDK, while server construction registers tools and resources only after the
runtime is available. HTTP transport is restricted to loopback and applies
origin validation; stdio remains the default.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `circuit_breaker`, `context_service`, `lint_service`, `wiki_surface` |
| `..api` | `LlmWikiApiError`, `build_documentation_query_service` |
| `..config` | `IDE_AGENTS`, `get_agent_config_path`, `read_config`, `validate_path`, `validate_source_root` |
| `.bootstrap_runtime` | `build_module_page_map` |
| `.concept_identity` | `ConceptIdentityError`, `validate_concept_uid`, `validate_natural_key` |
| `.documentation_queries` | `DocumentationQueryError` |
| `.documentation_query_builder` | `validate_live_query_source_selection` |
| `.extraction_service` | `InventoryRequest`, `get_inventory_result` |
| `.io` | `read_md` |
| `.knowledge_graph` | `CORE_RELATIONSHIP_KINDS`, `GRAPH_ORIGINS`, `GRAPH_RESOLUTIONS` |
| `.knowledge_observability` | `knowledge_status_payload`, `load_snapshot_knowledge_observability` |
| `.source_selection` | `SourceSelectionError`, `SourceSelectionPolicy`, `resolve_source_selection` |
| `.source_snapshot` | `SourceSnapshot`, `build_source_snapshot`, `capture_source_selection_inputs` |
| `.validation` | `posix_path_text`, `require_portable_relative_path` |
| `__future__` | `annotations` |
| `collections.abc` | `Iterable`, `Mapping` |
| `dataclasses` | `dataclass`, `field` |
| `ipaddress` | `ipaddress` |
| `json` | `json` |
| `mcp` | `mcp` |
| `mcp.server.fastmcp` | `FastMCP` |
| `pathlib` | `Path` |
| `re` | `re` |
| `sys` | `sys` |
| `typing` | `Any`, `Protocol`, `TypedDict`, `cast` |
| `urllib.parse` | `unquote`, `urlparse` |
| `uvicorn` | `uvicorn` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/mcp_server.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/mcp_server.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (1) |
| Outbound | `src` (17) |

### External packages

| Language | Used packages | Undeclared packages |
|---|---:|---:|
| python | 2 | 1 |

> All 18 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [MCPDependencyError](../entities/MCPDependencyError.md) | 98 | `RuntimeError` | Raised when the optional MCP runtime cannot be used. |
| [McpWikiError](../entities/McpWikiError.md) | 102 | `ValueError` | Raised for invalid MCP wiki requests. |
| [_SourceSelectionOptions](../entities/SourceSelectionOptions.md) | 106 | `TypedDict` | — |
| [_ExternalSourceOptions](../entities/ExternalSourceOptions.md) | 110 | `TypedDict` | — |
| [_McpHttpApplication](../entities/McpHttpApplication.md) | 114 | `Protocol` | — |
| [_RunnableMcpServer](../entities/RunnableMcpServer.md) | 122 | `Protocol` | — |
| [McpServerConfig](../entities/McpServerConfig.md) | 129 | — | — |
| [_SourceSelectionPin](../entities/SourceSelectionPin.md) | 142 | — | — |
| [WikiPage](../entities/mcp_server_WikiPage.md) | 161 | — | — |
| [OriginValidationMiddleware](../entities/OriginValidationMiddleware.md) | 248 | — | Minimal ASGI middleware that rejects unexpected browser origins. |
| [McpWikiService](../entities/McpWikiService.md) | 290 | — | Pure read/check operations exposed through MCP tools and resources. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_source_selection_pin` | `(policy: SourceSelectionPolicy \| None) -> _SourceSelectionPin` | — | — |
| `ensure_mcp_runtime` | `() -> None` | — | Validate that the optional MCP SDK can be imported on this runtime. |
| `validate_loopback_host` | `(host: str) -> None` | — | Reject non-loopback HTTP binds for local-only MCP v1. |
| `_is_loopback_host` | `(host: str) -> bool` | — | — |
| `_default_port_for_scheme` | `(scheme: str) -> int \| None` | — | — |
| `_normalise_origin` | `(origin: str) -> str` | — | — |
| `is_origin_allowed` | `(origin: str, *, port: int, allowed_origins: list[str] \| tuple[str, ...]) -> bool` | — | Return True when an HTTP Origin is acceptable for local MCP use. |
| `create_mcp_server` | `(config: McpServerConfig)` | — | Create and register the FastMCP server for a validated config. |
| `_register_mcp_tools` | `(server, service: McpWikiService) -> None` | — | — |
| `_register_mcp_resources` | `(server, service: McpWikiService) -> None` | — | — |
| `_register_root_resource` | `(server, service: McpWikiService, entry) -> None` | — | — |
| `_register_directory_resource` | `(server, service: McpWikiService, entry) -> None` | — | — |
| `run_mcp_server` | `(config: McpServerConfig) -> None` | — | Validate, build, and run the MCP server. |
| `_resource_uri` | `(kind: str, page_id: str) -> str` | — | — |
| `_graph_query_args` | `(query: Mapping[str, object]) -> tuple[str, str, int]` | — | — |
| `_knowledge_locator` | `(value: object) -> str` | — | — |
| `_knowledge_direction` | `(value: object) -> str` | — | — |
| `_section_ownership` | `(value: object) -> str \| None` | — | — |
| `_knowledge_kinds` | `(values: object) -> list[str] \| None` | — | — |
| `_typed_graph_direction` | `(value: object) -> str` | — | — |
| `_typed_graph_kinds` | `(values: object) -> list[str] \| None` | — | — |
| `_typed_graph_enum_values` | `(values: object, *, field: str, allowed: tuple[str, ...]) -> list[str] \| None` | — | — |
| `_bounded_query_limit` | `(value: object) -> int` | — | — |
| `_validate_page_id` | `(page_id: str) -> str` | — | — |
| `_is_safe_page_id` | `(page_id: str) -> bool` | — | — |
| `_normalise_source_path` | `(path: str) -> str` | — | — |
| `_ensure_inside` | `(root: Path, path: Path) -> None` | — | — |
| `_relative_posix` | `(path: Path, root: Path) -> str` | — | — |
| `_posix_string` | `(value: object) -> str` | — | — |
| `_normalise_report_paths` | `(payload: dict) -> None` | — | — |
| `_markdown_title` | `(content: str, fallback: str) -> str` | — | — |
| `_snippet` | `(content: str, start: int, length: int) -> str` | — | — |
| `_count_md` | `(path: Path) -> int` | — | — |
| `_count_surface_pages` | `(path: Path, entry) -> int` | — | — |
| `_installed_hooks` | `() -> list[str]` | — | — |
| `to_json` | `(data: object) -> str` | — | Serialize data as stable, human-readable JSON. |