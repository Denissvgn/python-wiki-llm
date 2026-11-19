# native_inspection Module

**Path:** `src/llm_wiki_cli/services/native_inspection.py`

## Description

One bounded concept inspection over one captured native read view.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `context_packet_builder` |
| `..api_types` | `QueryCostDisclosure` |
| `.documentation_queries` | `DocumentationQueryError`, `QUERY_RESULT_SERIALIZED_BYTE_LIMIT` |
| `.documentation_query_builder` | `build_documentation_query_service_from_view`, `build_snapshot_documentation_query_service` |
| `json` | `json` |
| `llm_wiki_engine.knowledge_coverage` | `MAX_COVERAGE_BYTES`, `build_knowledge_coverage` |
| `pathlib` | `Path` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/api_types.py"]
    n2["src/llm_wiki_cli/services/context_packet_builder.py"]
    n3["src/llm_wiki_cli/services/documentation_queries.py"]
    n4["src/llm_wiki_cli/services/documentation_query_builder.py"]
    n5["src/llm_wiki_cli/services/native_inspection.py"]
    n6["src/llm_wiki_engine/knowledge_coverage.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n0 --> n4
    n0 --> n5
    n0 --> n6
    n2 --> n3
    n2 --> n4
    n4 --> n2
    n4 --> n3
    n5 --> n1
    n5 --> n2
    n5 --> n3
    n5 --> n4
    n5 --> n6
    click n0 "../modules/api.md"
    click n1 "../modules/api_types.md"
    click n2 "../modules/context_packet_builder.md"
    click n3 "../modules/documentation_queries.md"
    click n4 "../modules/documentation_query_builder.md"
    click n5 "../modules/native_inspection.md"
    click n6 "../modules/knowledge_coverage.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Outbound | [api_types](../modules/api_types.md) |
| Outbound | [context_packet_builder](../modules/context_packet_builder.md) |
| Outbound | [documentation_queries](../modules/documentation_queries.md) |
| Outbound | [documentation_query_builder](../modules/documentation_query_builder.md) |
| Outbound | [knowledge_coverage](../modules/knowledge_coverage.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `inspect_native_concept` | `(coordinate: str, *, src_dir: str, wiki_root: Path, live: bool, limit: int, include_evidence: bool, allow_external_src: bool, source_selection: str \| Path \| None, helper_cache_dir: str \| Path \| None) -> dict[str, Any]` | — | Compose existing queries, then check that their common inputs still hold. |
