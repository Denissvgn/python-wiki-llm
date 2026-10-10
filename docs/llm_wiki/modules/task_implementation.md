# task_implementation Module

**Path:** `src/llm_wiki_cli/services/task_implementation.py`

## Description

Bind optional task implementation comparisons to their captured inputs.

## Imports

| Source | Symbols |
|--------|---------|
| `.implementation_evidence` | `validate_implementation_evidence`, `validate_implementation_comparison` |
| `.knowledge_envelope` | `ConsumedInput`, `hash_source_snapshot` |
| `.knowledge_evidence` | `is_valid_sha256` |
| `.knowledge_storage` | `canonical_bytes`, `digest`, `canonical_bytes`, `digest` |
| `.python_implementation` | `analysis_identity` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/implementation_evidence.py"]
    n1["src/llm_wiki_cli/services/knowledge_envelope.py"]
    n2["src/llm_wiki_cli/services/knowledge_evidence.py"]
    n3["src/llm_wiki_cli/services/knowledge_storage.py"]
    n4["src/llm_wiki_cli/services/python_implementation.py"]
    n5["src/llm_wiki_cli/services/task_context.py"]
    n6["src/llm_wiki_cli/services/task_context_v2.py"]
    n7["src/llm_wiki_cli/services/task_implementation.py"]
    n0 --> n4
    n1 --> n2
    n3 --> n0
    n3 --> n1
    n5 --> n1
    n5 --> n6
    n5 --> n7
    n6 --> n0
    n6 --> n1
    n6 --> n3
    n6 --> n4
    n6 --> n5
    n6 --> n7
    n7 --> n0
    n7 --> n1
    n7 --> n2
    n7 --> n3
    n7 --> n4
    click n0 "../modules/implementation_evidence.md"
    click n1 "../modules/knowledge_envelope.md"
    click n2 "../modules/knowledge_evidence.md"
    click n3 "../modules/knowledge_storage.md"
    click n4 "../modules/python_implementation.md"
    click n5 "../modules/task_context.md"
    click n6 "../modules/task_context_v2.md"
    click n7 "../modules/task_implementation.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [task_context](../modules/task_context.md) |
| Inbound | [task_context_v2](../modules/task_context_v2.md) |
| Outbound | [implementation_evidence](../modules/implementation_evidence.md) |
| Outbound | [knowledge_envelope](../modules/knowledge_envelope.md) |
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [python_implementation](../modules/python_implementation.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `native_bindings` | `(concepts)` | — | Extract owner bindings from consumed native records, never display names. |
| `attach_bindings` | `(body, bindings)` | — | — |
| `capture_receipt` | `(inventory_result)` | — | — |
| `_comparisons` | `(fact)` | — | — |
| `attach_capture` | `(body, inventory_result)` | — | — |
| `validate_task_implementations` | `(payload, settings)` | — | — |
