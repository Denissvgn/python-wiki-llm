# McpWikiService

**Location:** `src/llm_wiki_cli/services/mcp_server.py:435`
**Kind:** Class
**Bases:** —
**Module:** [mcp_server](../modules/mcp_server.md)

## Description

Workspace read/check operations with managed helper provisioning.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(src_dir: str = '.', wiki_dir: str = 'docs/llm_wiki', *, source_selection: str \| None = None, comparison_policy: str = 'auto', allow_external_src: bool = False, counter: TokenCounter \| None = None, workflow_policy: WorkflowPolicy \| None = None, workflow_profile: WorkflowProfile \| None = None, enable_sessions: bool = True, max_sessions: int = 8, helper_preparation: str = 'auto', helper_cache_dir: str \| None = None)` | — | — |
| `_assert_source_selection_pin_current` | `() -> SourceSelectionPolicy \| None` | — | — |
| `_assert_source_selection_current` | `() -> SourceSnapshot` | — | — |
| `_source_selection_options` | `() -> _SourceSelectionOptions` | — | — |
| `_external_source_options` | `() -> _ExternalSourceOptions` | — | — |
| `get_entity` | `(entity_id: str) -> dict` | `@_bound_operation` | — |
| `get_module` | `(module_id_or_source_path: str) -> dict` | `@_bound_operation` | — |
| `get_flow` | `(flow_id: str) -> dict` | `@_bound_operation` | — |
| `get_architecture_page` | `(page: str) -> dict` | `@_bound_operation` | — |
| `query_graph` | `(query: Mapping[str, object]) -> dict` | `@_bound_operation` | — |
| `query_documentation` | `(request: Mapping[str, Any]) -> dict` | `@_bound_operation` | Dispatch an exact bounded query through the shared API contract. |
| `get_concept` | `(locator_or_exact_route: str, limit: int = 20) -> dict` | `@_bound_operation` | Return one concept by current coordinate, durable UID, or alias. |
| `related_concepts` | `(locator_or_exact_route: str, direction: str = 'both', kinds: list[str] \| None = None, limit: int = 20) -> dict` | `@_bound_operation` | Return bounded relationships for one exact concept identity. |
| `list_concept_sections` | `(locator_or_exact_route: str, ownership: str \| None = None, limit: int = 20) -> dict` | `@_bound_operation` | Return bounded document-order sections for one exact concept. |
| `traverse_typed_graph` | `(locator_or_exact_route: str, direction: str = 'both', kinds: list[str] \| None = None, origins: list[str] \| None = None, resolutions: list[str] \| None = None, include_evidence: bool = False, limit: int = 20) -> dict` | `@_bound_operation` | Traverse bounded persisted typed relationships for one concept. |
| `explain_evidence` | `(locator_or_exact_route: str, limit: int = 20) -> dict` | `@_bound_operation` | Return bounded evidence for one exact concept identity. |
| `inspect_concept` | `(locator_or_exact_route: str, *, live: bool = False, limit: int = 20, include_evidence: bool = False) -> dict` | `@_bound_operation` | Inspect one native target from a shared snapshot or explicit live read. |
| `get_knowledge_coverage` | `(live: bool = False) -> dict` | `@_bound_operation` | Explain eligible observations without treating unmodeled content as drift. |
| `search_wiki` | `(query: str, kinds: list[str] \| None = None, limit: int = 20, mode: str = 'ranked', include_source: bool = False, discovery: str \| None = None) -> dict` | `@_bound_operation` | — |
| `build_budgeted_context` | `(request: Mapping[str, Any]) -> str` | `@_bound_operation` | Return precisely the canonical v3 text counted by the host counter. |
| `get_maintenance_queue` | `(limit: int = 30) -> dict` | `@_bound_operation` | — |
| `get_maintenance_status` | `(record_id: str \| None = None, limit: int = 30, live: bool = True) -> dict` | `@_bound_operation` | Read ordinary review state; mutations remain outside this MCP surface. |
| `build_task_context` | `(request: Mapping[str, Any]) -> str` | `@_bound_operation` | — |
| `open_context_session` | `() -> dict` | `@_bound_operation` | — |
| `_session` | `(session_id)` | — | — |
| `read_context_session` | `(session_id, request, *, if_result_id = None, delta = False)` | `@_bound_operation` | — |
| `read_compact_context_session` | `(session_id, request, view_options = None, *, if_result_id = None, if_view_id = None, delta = False)` | `@_bound_operation` | — |
| `get_task_context_receipt` | `(session_id, request_id, result_id, *, current = False)` | `@_bound_operation` | — |
| `hint_context_session` | `(session_id, *, unsaved_buffers = False)` | `@_bound_operation` | — |
| `close_context_session` | `(session_id)` | `@_bound_operation` | — |
| `close_sessions` | `()` | `@_bound_operation` | — |
| `get_context` | `(budget_tokens: int = 32000, focus: list[str] \| None = None, format: str = 'markdown', filters: dict \| None = None, prefer_fresh: bool = False, knowledge_mode: KnowledgeMode \| None = None) -> dict` | `@_bound_operation` | — |
| `get_context_packet` | `(budget_tokens: int = 32000, focus: list[str] \| None = None, format: str = 'json', filters: dict \| None = None, prefer_fresh: bool = False, if_packet_id: str \| None = None, knowledge_mode: KnowledgeMode \| None = None) -> dict` | `@_bound_operation` | Return a fresh qualified packet or an unchanged cache marker. |
| `check_wiki` | `(strict: bool = False, format: str = 'json', knowledge_drift_report: bool = False) -> dict` | `@_bound_operation` | — |
| `get_status` | `() -> dict` | `@_bound_operation` | — |
| `_run_documentation_query` | `(method_name: str, value: str, *, limit: int, **query_options) -> dict` | — | — |
| `read_resource` | `(uri: str) -> dict` | `@_bound_operation` | — |
| `list_resources` | `() -> list[dict]` | `@_bound_operation` | — |
| `_resolve_module_page_id` | `(value: str, *, source_snapshot: SourceSnapshot) -> str` | — | — |
| `_page_for` | `(kind: str, page_id: str) -> WikiPage` | — | — |
| `_page_from_uri` | `(uri: str) -> WikiPage` | — | — |
| `_read_page_result` | `(page: WikiPage) -> dict` | — | — |
| `_iter_pages` | `(kinds: set[str])` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["McpWikiService (src/llm_wiki_cli/services/mcp_server.py)"]
    n1["_register_directory_resource (src/llm_wiki_cli/services/mcp_server.py)"]
    n2["_register_mcp_resources (src/llm_wiki_cli/services/mcp_server.py)"]
    n3["_register_mcp_tools (src/llm_wiki_cli/services/mcp_server.py)"]
    n4["_register_root_resource (src/llm_wiki_cli/services/mcp_server.py)"]
    n5["create_mcp_server (src/llm_wiki_cli/services/mcp_server.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/mcp_server.md"
    click n1 "../modules/mcp_server.md"
    click n2 "../modules/mcp_server.md"
    click n3 "../modules/mcp_server.md"
    click n4 "../modules/mcp_server.md"
    click n5 "../modules/mcp_server.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [mcp_server](../modules/mcp_server.md) | 43 | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_register_directory_resource` | type_reference | [mcp_server](../modules/mcp_server.md) | — |
| `_register_mcp_resources` | type_reference | [mcp_server](../modules/mcp_server.md) | — |
| `_register_mcp_tools` | type_reference | [mcp_server](../modules/mcp_server.md) | — |
| `_register_root_resource` | type_reference | [mcp_server](../modules/mcp_server.md) | — |
| `create_mcp_server` | call | [mcp_server](../modules/mcp_server.md) | 1 |
