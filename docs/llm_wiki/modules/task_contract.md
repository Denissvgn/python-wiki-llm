# task_contract Module

**Path:** `src/llm_wiki_engine/task_contract.py`

## Description

Defines versioned task requests and detached canonical results. Normalization validates bounded text, exact coordinates, requirements and profile settings before workspace access. Provider task and request identities derive from normalized content; a host task label supplies attribution without granting authority.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `dataclasses` | `dataclass` |
| `json` | `json` |
| `llm_wiki_engine.context_request_format` | `validate_changes` |
| `llm_wiki_engine.query_request_format` | `normalize_concept_coordinate`, `normalize_supplied_paths` |
| `llm_wiki_engine.workflow_profile` | `WorkflowPolicy`, `WorkflowProfile`, `WorkflowRequestError`, `bounded_text`, `canonical_json`, `content_id`, `exact_fields`, `normalize_profile` |
| `types` | `MappingProxyType` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/services/behavior_reference.py"]
    n2["src/llm_wiki_cli/services/context_session.py"]
    n3["src/llm_wiki_cli/services/mcp_server.py"]
    n4["src/llm_wiki_cli/services/task_compact.py"]
    n5["src/llm_wiki_cli/services/task_context.py"]
    n6["src/llm_wiki_cli/services/task_context_v2.py"]
    n7["src/llm_wiki_engine/context_request_format.py"]
    n8["src/llm_wiki_engine/query_request_format.py"]
    n9["src/llm_wiki_engine/task_contract.py"]
    n10["src/llm_wiki_engine/workflow_profile.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n4
    n0 --> n5
    n0 --> n9
    n0 --> n10
    n1 --> n4
    n1 --> n9
    n2 --> n4
    n2 --> n5
    n2 --> n6
    n2 --> n9
    n2 --> n10
    n3 --> n0
    n3 --> n5
    n3 --> n9
    n3 --> n10
    n4 --> n5
    n4 --> n9
    n4 --> n10
    n5 --> n6
    n5 --> n9
    n5 --> n10
    n6 --> n5
    n6 --> n9
    n6 --> n10
    n9 --> n7
    n9 --> n8
    n9 --> n10
    click n0 "../modules/api.md"
    click n1 "../modules/behavior_reference.md"
    click n2 "../modules/context_session.md"
    click n3 "../modules/mcp_server.md"
    click n4 "../modules/task_compact.md"
    click n5 "../modules/task_context.md"
    click n6 "../modules/task_context_v2.md"
    click n7 "../modules/context_request_format.md"
    click n8 "../modules/query_request_format.md"
    click n9 "../modules/task_contract.md"
    click n10 "../modules/workflow_profile.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [behavior_reference](../modules/behavior_reference.md) |
| Inbound | [context_session](../modules/context_session.md) |
| Inbound | [mcp_server](../modules/mcp_server.md) |
| Inbound | [task_compact](../modules/task_compact.md) |
| Inbound | [task_context](../modules/task_context.md) |
| Inbound | [task_context_v2](../modules/task_context_v2.md) |
| Outbound | [context_request_format](../modules/context_request_format.md) |
| Outbound | [query_request_format](../modules/query_request_format.md) |
| Outbound | [workflow_profile](../modules/workflow_profile.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [TaskContext](../entities/TaskContext.md) | 123 | — | Detached canonical task output; unsuccessful budgets contain no context. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `coordinate` | `(kind: str, value: object) -> str` | — | — |
| `_array` | `(value: object, field: str) -> list` | — | — |
| `normalize_task_request` | `(request: Mapping[str, Any], *, profile: WorkflowProfile \| Mapping[str, Any] \| None = None, policy: WorkflowPolicy \| None = None) -> tuple[dict[str, Any], WorkflowProfile]` | — | — |
