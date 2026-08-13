# ProducerRecord

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:311`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_model](../modules/knowledge_model.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `ProducerRecord` in `src/llm_wiki_cli/services/knowledge_model.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `tool` | `ProducerComponent` | *required* | — |
| `extractors` | `tuple[ProducerComponent, ...]` | `()` | — |
| `plugins` | `tuple[ProducerComponent, ...]` | `()` | — |
| `extensions` | `Extensions` | `field(default_factory=dict)` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ProducerRecord (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["build_producer_record (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n2["_analysis_basis_hash (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n3["_downgrade_incompatible_tombstones (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n4["_validated_previous_producer (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n5["_parse_producer (src/llm_wiki_cli/services/knowledge_model.py)"]
    n6["_previous_committed_producer (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/knowledge_model.md"
    click n1 "../modules/knowledge_envelope.md"
    click n2 "../modules/knowledge_freshness.md"
    click n3 "../modules/knowledge_generation.md"
    click n4 "../modules/knowledge_generation.md"
    click n5 "../modules/knowledge_model.md"
    click n6 "../modules/knowledge_orchestration.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `extensions`, `extractors`, `plugins`, `tool` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `build_producer_record` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 1 |
| `build_producer_record` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `_analysis_basis_hash` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_downgrade_incompatible_tombstones` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_validated_previous_producer` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_parse_producer` | call | [knowledge_model](../modules/knowledge_model.md) | 1 |
| `_parse_producer` | type_reference | [knowledge_model](../modules/knowledge_model.md) | — |
| `_previous_committed_producer` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
