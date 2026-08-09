# BundleRecord

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:319`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_model](../modules/knowledge_model.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `BundleRecord` in `src/llm_wiki_cli/services/knowledge_model.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `repository` | `RepositoryRecord` | *required* | — |
| `snapshot` | `SnapshotRecord` | *required* | — |
| `producer` | `ProducerRecord` | *required* | — |
| `extensions` | `Extensions` | `field(default_factory=dict)` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["BundleRecord (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["_validated_bundle_payload (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n2["build_evaluated_envelope (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n3["_validate_live_producer (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n4["src/llm_wiki_cli/services/knowledge_index.py"]
    n5["_bundle_to_payload (src/llm_wiki_cli/services/knowledge_model.py)"]
    n6["_parse_bundle (src/llm_wiki_cli/services/knowledge_model.py)"]
    n7["_validate_index_references (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/knowledge_model.md"
    click n1 "../modules/knowledge_envelope.md"
    click n2 "../modules/knowledge_envelope.md"
    click n3 "../modules/knowledge_freshness.md"
    click n4 "../modules/knowledge_index.md"
    click n5 "../modules/knowledge_model.md"
    click n6 "../modules/knowledge_model.md"
    click n7 "../modules/knowledge_model.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `extensions`, `producer`, `repository`, `snapshot` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_validated_bundle_payload` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `build_evaluated_envelope` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_validate_live_producer` | call | [knowledge_freshness](../modules/knowledge_freshness.md) |
| `knowledge_index` | import | [knowledge_index](../modules/knowledge_index.md) |
| `_bundle_to_payload` | type_reference | [knowledge_model](../modules/knowledge_model.md) |
| `_parse_bundle` | call | [knowledge_model](../modules/knowledge_model.md) |
| `_parse_bundle` | type_reference | [knowledge_model](../modules/knowledge_model.md) |
| `_validate_index_references` | type_reference | [knowledge_model](../modules/knowledge_model.md) |
