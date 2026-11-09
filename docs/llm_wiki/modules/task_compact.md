# task_compact Module

**Path:** `src/llm_wiki_cli/services/task_compact.py`

## Description

Pure, canonical-bound task presentation with separately counted view budgets.

View request v1 selects the encoded compact-v1 projection. View request v2
selects [readable selected evidence](task_compact_readable.md) with full fact
objects and canonical limitations, requiring no observation codec/codebook.
Both validate original canonical evidence and retain exact request/profile,
counter, budget and view identity binding. A budget failure emits a separately
counted diagnostic and preserves the available canonical receipt. Presentation
performs no source reads; delivery uses the owned task/session lifecycle.

## Imports

| Source | Symbols |
|--------|---------|
| `.context_budget` | `_accounted_render` |
| `.immutable` | `freeze` |
| `.request_json` | `_pairs`, `_constant` |
| `.task_compact_readable` | `readable_projection`, `readable_expansion` |
| `.task_context` | `validate_task_context`, `_counter`, `_LIMITATIONS` |
| `.task_contract` | `TaskContext`, `TASK_REQUEST_SCHEMA_V2`, `normalize_task_request` |
| `.workflow_profile` | `canonical_json`, `content_id` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `copy` | `deepcopy` |
| `dataclasses` | `dataclass` |
| `json` | `json` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/services/behavior_reference.py"]
    n2["src/llm_wiki_cli/services/context_budget.py"]
    n3["src/llm_wiki_cli/services/context_session.py"]
    n4["src/llm_wiki_cli/services/immutable.py"]
    n5["src/llm_wiki_cli/services/request_json.py"]
    n6["src/llm_wiki_cli/services/task_compact.py"]
    n7["src/llm_wiki_cli/services/task_compact_delivery.py"]
    n8["src/llm_wiki_cli/services/task_compact_readable.py"]
    n9["src/llm_wiki_cli/services/task_context.py"]
    n10["src/llm_wiki_cli/services/task_contract.py"]
    n11["src/llm_wiki_cli/services/workflow_profile.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n0 --> n6
    n0 --> n7
    n0 --> n9
    n0 --> n10
    n0 --> n11
    n1 --> n6
    n1 --> n10
    n2 --> n5
    n3 --> n4
    n3 --> n6
    n3 --> n9
    n3 --> n10
    n3 --> n11
    n6 --> n2
    n6 --> n4
    n6 --> n5
    n6 --> n8
    n6 --> n9
    n6 --> n10
    n6 --> n11
    n7 --> n3
    n7 --> n6
    n9 --> n2
    n9 --> n5
    n9 --> n10
    n9 --> n11
    n10 --> n11
    n11 --> n5
    click n0 "../modules/api.md"
    click n1 "../modules/behavior_reference.md"
    click n2 "../modules/context_budget.md"
    click n3 "../modules/context_session.md"
    click n4 "../modules/immutable.md"
    click n5 "../modules/request_json.md"
    click n6 "../modules/task_compact.md"
    click n7 "../modules/task_compact_delivery.md"
    click n8 "../modules/task_compact_readable.md"
    click n9 "../modules/task_context.md"
    click n10 "../modules/task_contract.md"
    click n11 "../modules/workflow_profile.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [behavior_reference](../modules/behavior_reference.md) |
| Inbound | [context_session](../modules/context_session.md) |
| Inbound | [task_compact_delivery](../modules/task_compact_delivery.md) |
| Outbound | [context_budget](../modules/context_budget.md) |
| Outbound | [immutable](../modules/immutable.md) |
| Outbound | [request_json](../modules/request_json.md) |
| Outbound | [task_compact_readable](../modules/task_compact_readable.md) |
| Outbound | [task_context](../modules/task_context.md) |
| Outbound | [task_contract](../modules/task_contract.md) |
| Outbound | [workflow_profile](../modules/workflow_profile.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [TaskCompactError](../entities/TaskCompactError.md) | 78 | `ValueError` | — |
| [CompactTaskContext](../entities/CompactTaskContext.md) | 85 | — | — |
| [_CheckedCounter](../entities/CheckedCounter.md) | 141 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_encode_limits` | `(values)` | — | — |
| `_decode_limits` | `(values)` | — | — |
| `normalize_view_options` | `(value, *, ceiling)` | — | — |
| `_validated` | `(canonical_text, request, profile, policy, counter)` | — | — |
| `_same` | `(first, second)` | — | — |
| `_encode_contract` | `(value)` | — | Only explicit, present known defaults can use a reversible codec. |
| `_decode_contract` | `(value)` | — | — |
| `_encode_observation` | `(facet, value)` | — | — |
| `_decode_observation` | `(value)` | — | — |
| `_projection` | `(canonical, request)` | — | — |
| `_expanded` | `(payload)` | — | — |
| `render_compact_task_context` | `(canonical_text, request, *, view_options, profile = None, policy = None, counter = None)` | — | — |
| `validate_compact_task_context` | `(compact_text, canonical_text, request, *, view_options, profile = None, policy = None, counter = None)` | — | — |
| `expand_compact_task_context` | `(compact_text, canonical_text, request, *, view_options, profile = None, policy = None, counter = None)` | — | — |