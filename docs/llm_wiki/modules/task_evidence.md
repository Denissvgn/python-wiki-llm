# task_evidence Module

**Path:** `src/llm_wiki_cli/services/task_evidence.py`

## Description

Selects source contracts and qualified query observations from an existing capture. Exact owner and occurrence coordinates preserve ambiguity, declaration kinds and signature grouping. Canonical fact identities deduplicate equivalent declarations, and requirement coverage refers only to evidence actually emitted.

## Imports

| Source | Symbols |
|--------|---------|
| `.documentation_query_builder` | `build_documentation_query_service_from_view` |
| `.implementation_evidence` | `select_implementation_comparison` |
| `__future__` | `annotations` |
| `collections` | `Counter` |
| `llm_wiki_engine` | `context_packet` |
| `llm_wiki_engine.markdown_sections` | `parse_markdown_document` |
| `llm_wiki_engine.workflow_profile` | `content_id` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/documentation_query_builder.py"]
    n1["src/llm_wiki_cli/services/implementation_evidence.py"]
    n2["src/llm_wiki_cli/services/task_context.py"]
    n3["src/llm_wiki_cli/services/task_context_v2.py"]
    n4["src/llm_wiki_cli/services/task_evidence.py"]
    n5["src/llm_wiki_engine/context_packet.py"]
    n6["src/llm_wiki_engine/markdown_sections.py"]
    n7["src/llm_wiki_engine/workflow_profile.py"]
    n2 --> n0
    n2 --> n3
    n2 --> n4
    n2 --> n5
    n2 --> n7
    n3 --> n0
    n3 --> n1
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n3 --> n7
    n4 --> n0
    n4 --> n1
    n4 --> n5
    n4 --> n6
    n4 --> n7
    click n0 "../modules/documentation_query_builder.md"
    click n1 "../modules/implementation_evidence.md"
    click n2 "../modules/task_context.md"
    click n3 "../modules/task_context_v2.md"
    click n4 "../modules/task_evidence.md"
    click n5 "../modules/context_packet.md"
    click n6 "../modules/markdown_sections.md"
    click n7 "../modules/workflow_profile.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [task_context](../modules/task_context.md) |
| Inbound | [task_context_v2](../modules/task_context_v2.md) |
| Outbound | [documentation_query_builder](../modules/documentation_query_builder.md) |
| Outbound | [implementation_evidence](../modules/implementation_evidence.md) |
| Outbound | [context_packet](../modules/context_packet.md) |
| Outbound | [markdown_sections](../modules/markdown_sections.md) |
| Outbound | [workflow_profile](../modules/workflow_profile.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `declaration_records` | `(inventory)` | — | Index extractor-owned contracts without re-parsing source code. |
| `match_declarations` | `(records, selector)` | — | — |
| `query_service` | `(captured, limit)` | — | — |
| `observe_requirement` | `(captured, service, records, requirement, *, scope, limit)` | — | — |
| `coverage` | `(requirements, observations, facts)` | — | — |
