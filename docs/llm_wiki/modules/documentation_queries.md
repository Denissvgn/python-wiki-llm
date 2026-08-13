# documentation_queries Module

**Path:** `src/llm_wiki_cli/services/documentation_queries.py`

## Description

Pure documentation graph query helpers.

This module indexes already-built inventory, call graph, data-flow, dependency,
and wiki-surface payloads. It intentionally performs no file writes, file reads,
network calls, or adapter registration so CLI, Python API, MCP, and context
surfaces can consume the same deterministic query answers later.

## Imports

| Source | Symbols |
|--------|---------|
| `.contracts` | `SECTION_OWNERSHIP_EXTENSION_KEY` |
| `.dependencies` | `build_dependency_graph`, `dependency_metrics`, `detect_cycles`, `topological_order` |
| `.knowledge_consumption` | `KnowledgeAvailability`, `KnowledgeReadReason`, `KnowledgeReadView` |
| `.knowledge_governance` | `GOVERNANCE_EXTENSION_KEY` |
| `.knowledge_graph` | `CORE_RELATIONSHIP_KINDS`, `GRAPH_ORIGINS`, `GRAPH_RESOLUTIONS`, `KnowledgeGraphError`, `typed_graph_from_knowledge_extensions` |
| `.knowledge_model` | `knowledge_index_to_payload` |
| `.knowledge_observability` | `knowledge_freshness_hint`, `knowledge_status_payload` |
| `.relationships` | `build_entity_relationship_summaries` |
| `.validation` | `normalize_legacy_portable_relative_path`, `require_nonempty_text` |
| `__future__` | `annotations` |
| `collections` | `defaultdict` |
| `collections.abc` | `Iterable` |
| `dataclasses` | `dataclass` |
| `enum` | `Enum` |
| `functools` | `wraps` |
| `itertools` | `islice` |
| `json` | `json` |
| `pathlib` | `PurePosixPath` |
| `re` | `re` |
| `typing` | `Any`, `Callable`, `Iterable`, `Mapping`, `Optional`, `ParamSpec`, `Sequence`, `cast` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/documentation_queries.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/documentation_queries.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (8) |
| Outbound | `src` (9) |

> All 17 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [DocumentationQueryError](../entities/DocumentationQueryError.md) | 128 | `ValueError` | Raised when a documentation graph query request is invalid. |
| [_BoundedResult](../entities/BoundedResult.md) | 342 | — | One deterministic collection plus its exact response bounds. |
| [DocumentationGraphQueryService](../entities/DocumentationGraphQueryService.md) | 832 | — | Read-only graph query service over already-derived documentation payloads. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `knowledge_view_selection_eligible` | `(knowledge_view: KnowledgeReadView \| None, *, basis_incompatible: bool = False) -> bool` | — | Return whether a captured projection is safe for native selection. |
| `_ineligible_knowledge_status` | `(knowledge_view: KnowledgeReadView) -> tuple[str, str]` | — | — |
| `_truncate_utf8` | `(value: str, limit: int) -> str` | — | Return a deterministic UTF-8 prefix that never exceeds ``limit`` bytes. |
| `_cap_query_result_strings` | `(value: object, limit: int, *, field: str \| None = None) -> object` | — | — |
| `_query_result_byte_bound` | `(total: int, returned: int) -> dict[str, int \| bool]` | — | — |
| `_attach_query_result_byte_bound` | `(result: dict[str, Any], *, total: int) -> tuple[dict[str, Any], int]` | — | — |
| `_minimal_oversized_query_result` | `(result: Mapping[str, Any], *, total_bytes: int) -> dict[str, Any]` | — | Preserve query status while omitting every oversized returned record. |
| `_fit_query_result` | `(result: dict[str, Any]) -> dict[str, Any]` | — | Enforce a shared serialized-byte ceiling for every public query result. |
| `fit_documentation_query_result` | `(result: Mapping[str, Any]) -> dict[str, Any]` | — | Return a detached public query payload within the shared byte limit. |
| `_bounded_query_result` | `(method: Callable[_QueryParameters, dict[str, Any]]) -> Callable[_QueryParameters, dict[str, Any]]` | — | — |
| `_text_key` | `(value: object) -> tuple[str, str]` | — | — |
| `_value_key` | `(value: object) -> tuple` | — | — |
| `_record_sort_key` | `(record: Mapping[str, Any]) -> tuple` | — | — |
| `_jsonable` | `(value: object) -> object` | — | — |
| `_jsonable_mapping` | `(value: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_jsonable_mapping_list` | `(values: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` | — | — |
| `_require_query` | `(value: object, field: str) -> str` | — | Retain query-request whitespace normalization for API compatibility. |
| `_query_identity_within_limit` | `(query: str, field: str) -> str` | — | Enforce the public query-identity byte ceiling. |
| `_normalise_source_path` | `(value: object, *, field: str, required: bool) -> Optional[str]` | — | — |
| `_module_name` | `(filepath: Optional[str]) -> Optional[str]` | — | — |
| `_callable_ref` | `(summary: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_class_ref` | `(summary: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_flow_ref` | `(flow: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_page_ref` | `(page: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_edge_pair` | `(edge: object) -> Optional[tuple[str, str]]` | — | — |
| `_call_endpoint_ref` | `(endpoint: Mapping[str, Any], edge: Mapping[str, Any]) -> dict` | — | — |
| `_dedupe_sorted_all` | `(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` | — | — |
| `_summary_relationship_records` | `(summary: Mapping[str, Any], field: str) -> list[dict[str, Any]]` | — | — |
| `_wire_value` | `(value: object) -> object` | — | — |
| `_canonical_json` | `(value: object) -> str` | — | — |
| `_raw_evidence_byte_bound` | `(value: object) -> dict[str, int \| bool]` | — | — |
| `_knowledge_target_ref` | `(target: Mapping[str, Any], resolution: object) -> dict[str, Any]` | — | Return only the coordinates needed to understand a compact target. |
| `_compact_context_endpoint` | `(value: object, *, include_normalized_target: bool = False, source_canonical_path: str \| None = None) -> dict[str, Any]` | — | Project graph coordinates without raw target text or stored diagnostics. |
| `_safe_context_coordinate_text` | `(value: object, *, limit: int) -> str \| None` | — | — |
| `_safe_context_asset_path` | `(source_canonical_path: str, value: object) -> str \| None` | — | — |
| `_safe_normalized_context_target` | `(value: object) -> str \| None` | — | — |
| `_compact_context_coverage` | `(value: Mapping[str, Any]) -> dict[str, Any]` | — | Retain bounded graph coverage while omitting operational samples. |
| `_compact_context_graph_status` | `(value: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_compact_context_page` | `(value: Mapping[str, Any]) -> dict[str, str] \| None` | — | Return the exact bounded page coordinates permitted on the v2 wire. |
| `_freshness_basis_payload` | `(value: object) -> Optional[dict[str, Any]]` | — | — |
