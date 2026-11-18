# task_implementation Module

**Path:** `src/llm_wiki_cli/services/task_implementation.py`

## Description

Bind optional task implementation comparisons to their captured inputs.

## Imports

| Source | Symbols |
|--------|---------|
| `.implementation_evidence` | `validate_implementation_evidence`, `validate_implementation_comparison` |
| `.python_implementation` | `analysis_identity` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `llm_wiki_engine.knowledge_envelope` | `ConsumedInput`, `hash_source_snapshot` |
| `llm_wiki_engine.knowledge_evidence` | `is_valid_sha256` |
| `llm_wiki_engine.knowledge_storage` | `canonical_bytes`, `digest`, `canonical_bytes`, `digest` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/implementation_evidence.py"]
    n1["src/llm_wiki_cli/services/python_implementation.py"]
    n2["src/llm_wiki_cli/services/task_context.py"]
    n3["src/llm_wiki_cli/services/task_context_v2.py"]
    n4["src/llm_wiki_cli/services/task_implementation.py"]
    n5["src/llm_wiki_engine/knowledge_envelope.py"]
    n6["src/llm_wiki_engine/knowledge_evidence.py"]
    n7["src/llm_wiki_engine/knowledge_storage.py"]
    n0 --> n1
    n0 --> n6
    n2 --> n3
    n2 --> n4
    n2 --> n5
    n3 --> n0
    n3 --> n1
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n3 --> n7
    n4 --> n0
    n4 --> n1
    n4 --> n5
    n4 --> n6
    n4 --> n7
    n5 --> n6
    n7 --> n5
    click n0 "../modules/implementation_evidence.md"
    click n1 "../modules/python_implementation.md"
    click n2 "../modules/task_context.md"
    click n3 "../modules/task_context_v2.md"
    click n4 "../modules/task_implementation.md"
    click n5 "../modules/knowledge_envelope.md"
    click n6 "../modules/knowledge_evidence.md"
    click n7 "../modules/knowledge_storage.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [task_context](../modules/task_context.md) |
| Inbound | [task_context_v2](../modules/task_context_v2.md) |
| Outbound | [implementation_evidence](../modules/implementation_evidence.md) |
| Outbound | [python_implementation](../modules/python_implementation.md) |
| Outbound | [knowledge_envelope](../modules/knowledge_envelope.md) |
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `native_bindings` | `(concepts)` | — | Extract owner bindings from consumed native records, never display names. |
| `attach_bindings` | `(body, bindings)` | — | — |
| `capture_receipt` | `(inventory_result)` | — | — |
| `_comparisons` | `(fact)` | — | — |
| `attach_capture` | `(body, inventory_result)` | — | — |
| `validate_task_implementations` | `(payload, settings)` | — | — |
