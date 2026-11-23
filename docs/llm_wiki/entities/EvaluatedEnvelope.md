# EvaluatedEnvelope

**Location:** `src/llm_wiki_engine/knowledge_envelope.py:268`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_envelope](../modules/knowledge_envelope.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Version-tagged evaluated basis committed through manifest v5.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `bundle` | `BundleRecord` | *required* | — |
| `schema_version` | `str` | `EVALUATED_ENVELOPE_VERSION` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `inventory_hash` | `() -> str` | `@property` | — |
| `to_payload` | `() -> dict[str, Any]` | — | — |
| `to_json` | `() -> str` | — | — |
| `content_hash` | `() -> str` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["EvaluatedEnvelope (src/llm_wiki_engine/knowledge_envelope.py)"]
    n1["_project (src/llm_wiki_cli/services/historical_release.py)"]
    n2["_application_knowledge_extensions (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n3["_stabilize_revision_only_noop (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n4["predecessor_records (src/llm_wiki_engine/historical_sources.py)"]
    n5["_validate_artifact_parity (src/llm_wiki_engine/knowledge_artifacts.py)"]
    n6["build_evaluated_envelope (src/llm_wiki_engine/knowledge_envelope.py)"]
    n7["evaluated_envelope_to_payload (src/llm_wiki_engine/knowledge_envelope.py)"]
    n8["hash_evaluated_envelope (src/llm_wiki_engine/knowledge_envelope.py)"]
    n9["serialize_evaluated_envelope (src/llm_wiki_engine/knowledge_envelope.py)"]
    n10["src/llm_wiki_engine/knowledge_index.py"]
    n11["_capture_slice (src/llm_wiki_engine/knowledge_storage_access.py)"]
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
    click n1 "../modules/historical_release.md"
    click n2 "../modules/knowledge_generation.md"
    click n3 "../modules/knowledge_orchestration.md"
    click n4 "../modules/historical_sources.md"
    click n5 "../modules/knowledge_artifacts.md"
    click n6 "../modules/knowledge_envelope.md"
    click n7 "../modules/knowledge_envelope.md"
    click n8 "../modules/knowledge_envelope.md"
    click n9 "../modules/knowledge_envelope.md"
    click n10 "../modules/knowledge_index.md"
    click n11 "../modules/knowledge_storage_access.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_envelope](../modules/knowledge_envelope.md) | 4 | `bundle`, `schema_version` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_project` | call | [historical_release](../modules/historical_release.md) | 1 |
| `_application_knowledge_extensions` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_stabilize_revision_only_noop` | call | [knowledge_orchestration](../modules/knowledge_orchestration.md) | 1 |
| `predecessor_records` | call | [historical_sources](../modules/historical_sources.md) | 1 |
| `_validate_artifact_parity` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 1 |
| `build_evaluated_envelope` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 1 |
| `build_evaluated_envelope` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `evaluated_envelope_to_payload` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `hash_evaluated_envelope` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `serialize_evaluated_envelope` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `knowledge_index` | import | [knowledge_index](../modules/knowledge_index.md) | — |
| `_capture_slice` | call | [knowledge_storage_access](../modules/knowledge_storage_access.md) | 1 |

> References: showing 12 of 13 logical references; 1 omitted by the 12-row generated summary limit.
