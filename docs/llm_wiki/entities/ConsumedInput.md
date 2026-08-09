# ConsumedInput

**Location:** `src/llm_wiki_cli/services/knowledge_envelope.py:123`
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
    n0["ConsumedInput (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n1["_live_source_snapshot_hash (src/llm_wiki_cli/services/documentation_native.py)"]
    n2["_canonical_consumed_input_kind (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n3["_validate_inventory_source_parity (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n4["consumed_inputs_from_captured_hashes (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n5["ConsumedInput.from_bytes (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n6["hash_source_snapshot (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n7["_validated_consumed_inputs (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n8["_merge_explicit_consumed_input (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n9["runtime_consumed_inputs (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/knowledge_envelope.md"
    click n1 "../modules/documentation_native.md"
    click n2 "../modules/knowledge_envelope.md"
    click n3 "../modules/knowledge_envelope.md"
    click n4 "../modules/knowledge_envelope.md"
    click n5 "../modules/knowledge_envelope.md"
    click n6 "../modules/knowledge_envelope.md"
    click n7 "../modules/knowledge_generation.md"
    click n8 "../modules/knowledge_orchestration.md"
    click n9 "../modules/knowledge_orchestration.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_envelope](../modules/knowledge_envelope.md) | 3 | `content_hash`, `kind`, `path` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_live_source_snapshot_hash` | call | [documentation_native](../modules/documentation_native.md) |
| `_live_source_snapshot_hash` | call | [documentation_native](../modules/documentation_native.md) |
| `_canonical_consumed_input_kind` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_validate_inventory_source_parity` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `consumed_inputs_from_captured_hashes` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `consumed_inputs_from_captured_hashes` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `ConsumedInput.from_bytes` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `hash_source_snapshot` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_validated_consumed_inputs` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) |
| `_merge_explicit_consumed_input` | call | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| `_merge_explicit_consumed_input` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| `runtime_consumed_inputs` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
