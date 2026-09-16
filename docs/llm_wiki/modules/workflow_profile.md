# workflow_profile Module

**Path:** `src/llm_wiki_cli/services/workflow_profile.py`

## Description

Normalizes explicitly supplied workflow settings within immutable host ceilings. Profiles can narrow permitted scope and resource use, but cannot select roots, load tokenizer paths, prepare helpers or authorize execution. Native availability, freshness preference and semantic judgment retain distinct meanings.

## Imports

| Source | Symbols |
|--------|---------|
| `.request_json` | `load_request` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `dataclasses` | `dataclass`, `fields` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `pathlib` | `Path` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/services/context_session.py"]
    n2["src/llm_wiki_cli/services/mcp_server.py"]
    n3["src/llm_wiki_cli/services/request_json.py"]
    n4["src/llm_wiki_cli/services/task_context.py"]
    n5["src/llm_wiki_cli/services/task_context_v2.py"]
    n6["src/llm_wiki_cli/services/task_contract.py"]
    n7["src/llm_wiki_cli/services/task_evidence.py"]
    n8["src/llm_wiki_cli/services/workflow_profile.py"]
    n0 --> n1
    n0 --> n4
    n0 --> n6
    n0 --> n8
    n1 --> n4
    n1 --> n6
    n1 --> n8
    n2 --> n0
    n2 --> n8
    n4 --> n3
    n4 --> n5
    n4 --> n6
    n4 --> n7
    n4 --> n8
    n5 --> n4
    n5 --> n6
    n5 --> n7
    n5 --> n8
    n6 --> n8
    n7 --> n8
    n8 --> n3
    click n0 "../modules/api.md"
    click n1 "../modules/context_session.md"
    click n2 "../modules/mcp_server.md"
    click n3 "../modules/request_json.md"
    click n4 "../modules/task_context.md"
    click n5 "../modules/task_context_v2.md"
    click n6 "../modules/task_contract.md"
    click n7 "../modules/task_evidence.md"
    click n8 "../modules/workflow_profile.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [context_session](../modules/context_session.md) |
| Inbound | [mcp_server](../modules/mcp_server.md) |
| Inbound | [task_context](../modules/task_context.md) |
| Inbound | [task_context_v2](../modules/task_context_v2.md) |
| Inbound | [task_contract](../modules/task_contract.md) |
| Inbound | [task_evidence](../modules/task_evidence.md) |
| Outbound | [request_json](../modules/request_json.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [WorkflowRequestError](../entities/WorkflowRequestError.md) | 28 | `ValueError` | A workflow request is invalid before any workspace access. |
| [WorkflowPolicy](../entities/WorkflowPolicy.md) | 92 | — | Trusted host ceilings; profiles and task data can only narrow these. |
| [WorkflowProfile](../entities/WorkflowProfile.md) | 113 | — | Immutable explicit settings; each payload access returns detached data. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `canonical_json` | `(value: Any) -> bytes` | — | — |
| `content_id` | `(domain: str, value: Any) -> str` | — | — |
| `bounded_int` | `(value: object, field: str, maximum: int, *, minimum: int = 1) -> int` | — | — |
| `bounded_text` | `(value: object, field: str, maximum: int = 4096, *, empty: bool = False) -> str` | — | — |
| `exact_fields` | `(value: object, allowed: set[str], field: str) -> dict[str, Any]` | — | — |
| `_settings` | `(value: object) -> dict[str, Any]` | — | — |
| `normalize_profile` | `(profile: WorkflowProfile \| Mapping[str, Any] \| None = None, *, policy: WorkflowPolicy \| None = None, overrides: Mapping[str, Any] \| None = None) -> WorkflowProfile` | — | — |
| `load_profile` | `(path: str \| Path, *, policy: WorkflowPolicy \| None = None) -> WorkflowProfile` | — | Load only the explicitly named profile file; no ambient discovery. |