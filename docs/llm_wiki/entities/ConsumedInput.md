# ConsumedInput

**Location:** `src/llm_wiki_engine/knowledge_envelope.py:126`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_envelope](../modules/knowledge_envelope.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One already captured repository-relative content commitment.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `path` | `str` | *required* | — |
| `content_hash` | `str` | *required* | — |
| `kind` | `ConsumedInputKind \| str` | `ConsumedInputKind.SOURCE` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `from_bytes` | `(path: str, content: bytes, *, kind: ConsumedInputKind \| str = ConsumedInputKind.SOURCE) -> ConsumedInput` | `@classmethod` | Capture exact bytes without retaining them in the envelope input. |
| `kind_value` | `() -> str` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ConsumedInput (src/llm_wiki_engine/knowledge_envelope.py)"]
    n1["_live_source_snapshot_hash (src/llm_wiki_cli/services/documentation_native.py)"]
    n2["_validated_consumed_inputs (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n3["_merge_explicit_consumed_input (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n4["runtime_consumed_inputs (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n5["recover_maintenance_authority (src/llm_wiki_cli/services/maintenance_service.py)"]
    n6["src/llm_wiki_cli/services/source_snapshot.py"]
    n7["validate_scoped_bindings (src/llm_wiki_cli/services/task_context_v2.py)"]
    n8["validate_task_implementations (src/llm_wiki_cli/services/task_implementation.py)"]
    n9["_canonical_consumed_input_kind (src/llm_wiki_engine/knowledge_envelope.py)"]
    n10["_validate_inventory_source_parity (src/llm_wiki_engine/knowledge_envelope.py)"]
    n11["consumed_inputs_from_captured_hashes (src/llm_wiki_engine/knowledge_envelope.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    click n0 "../modules/knowledge_envelope.md"
    click n1 "../modules/documentation_native.md"
    click n2 "../modules/knowledge_generation.md"
    click n3 "../modules/knowledge_orchestration.md"
    click n4 "../modules/knowledge_orchestration.md"
    click n5 "../modules/maintenance_service.md"
    click n6 "../modules/source_snapshot.md"
    click n7 "../modules/task_context_v2.md"
    click n8 "../modules/task_implementation.md"
    click n9 "../modules/knowledge_envelope.md"
    click n10 "../modules/knowledge_envelope.md"
    click n11 "../modules/knowledge_envelope.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_envelope](../modules/knowledge_envelope.md) | 3 | `content_hash`, `kind`, `path` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_live_source_snapshot_hash` | call | [documentation_native](../modules/documentation_native.md) | 2 |
| `_validated_consumed_inputs` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_merge_explicit_consumed_input` | call | [knowledge_orchestration](../modules/knowledge_orchestration.md) | 1 |
| `_merge_explicit_consumed_input` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `runtime_consumed_inputs` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `recover_maintenance_authority` | call | [maintenance_service](../modules/maintenance_service.md) | 1 |
| `source_snapshot` | import | [source_snapshot](../modules/source_snapshot.md) | — |
| `validate_scoped_bindings` | call | [task_context_v2](../modules/task_context_v2.md) | 1 |
| `validate_task_implementations` | call | [task_implementation](../modules/task_implementation.md) | 1 |
| `_canonical_consumed_input_kind` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `_validate_inventory_source_parity` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `consumed_inputs_from_captured_hashes` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 1 |

> References: showing 12 of 16 logical references; 4 omitted by the 12-row generated summary limit.
