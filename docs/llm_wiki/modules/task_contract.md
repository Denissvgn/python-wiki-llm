# task_contract Module

**Path:** `src/llm_wiki_cli/services/task_contract.py`

## Description

Defines versioned task requests and detached canonical results. Normalization validates bounded text, exact coordinates, requirements and profile settings before workspace access. Provider task and request identities derive from normalized content; a host task label supplies attribution without granting authority.

## Imports

| Source | Symbols |
|--------|---------|
| `.change_selection` | `validate_changes` |
| `.documentation_query_builder` | `normalize_concept_coordinate`, `normalize_supplied_paths` |
| `.workflow_profile` | `WorkflowPolicy`, `WorkflowProfile`, `WorkflowRequestError`, `bounded_text`, `canonical_json`, `content_id`, `exact_fields`, `normalize_profile` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `dataclasses` | `dataclass` |
| `json` | `json` |
| `types` | `MappingProxyType` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/services/change_selection.py"]
    n2["src/llm_wiki_cli/services/context_session.py"]
    n3["src/llm_wiki_cli/services/documentation_query_builder.py"]
    n4["src/llm_wiki_cli/services/task_context.py"]
    n5["src/llm_wiki_cli/services/task_contract.py"]
    n6["src/llm_wiki_cli/services/workflow_profile.py"]
    n0 --> n2
    n0 --> n3
    n0 --> n4
    n0 --> n5
    n0 --> n6
    n2 --> n4
    n2 --> n5
    n2 --> n6
    n4 --> n1
    n4 --> n3
    n4 --> n5
    n4 --> n6
    n5 --> n1
    n5 --> n3
    n5 --> n6
    click n0 "../modules/api.md"
    click n1 "../modules/change_selection.md"
    click n2 "../modules/context_session.md"
    click n3 "../modules/documentation_query_builder.md"
    click n4 "../modules/task_context.md"
    click n5 "../modules/task_contract.md"
    click n6 "../modules/workflow_profile.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [context_session](../modules/context_session.md) |
| Inbound | [task_context](../modules/task_context.md) |
| Outbound | [change_selection](../modules/change_selection.md) |
| Outbound | [documentation_query_builder](../modules/documentation_query_builder.md) |
| Outbound | [workflow_profile](../modules/workflow_profile.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [TaskContext](../entities/TaskContext.md) | 106 | — | Detached canonical task output; unsuccessful budgets contain no context. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `coordinate` | `(kind: str, value: object) -> str` | — | — |
| `_array` | `(value: object, field: str) -> list` | — | — |
| `normalize_task_request` | `(request: Mapping[str, Any], *, profile: WorkflowProfile \| Mapping[str, Any] \| None = None, policy: WorkflowPolicy \| None = None) -> tuple[dict[str, Any], WorkflowProfile]` | — | — |