# KnowledgeIndex

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:450`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_model](../modules/knowledge_model.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `KnowledgeIndex` in `src/llm_wiki_cli/services/knowledge_model.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `schema_version` | `str` | *required* | — |
| `bundle` | `BundleRecord` | *required* | — |
| `concepts` | `tuple[ConceptRecord, ...]` | *required* | — |
| `relationships` | `tuple[RelationshipRecord, ...]` | *required* | — |
| `extensions` | `Extensions` | `field(default_factory=dict)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `from_payload` | `(payload: object) -> 'KnowledgeIndex'` | `@classmethod` | — |
| `to_payload` | `() -> dict[str, Any]` | — | — |
| `to_json` | `() -> str` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeIndex (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["_concept_for_uid (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n2["_scope_locator_for_uid (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n3["_status_payload (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n4["_source_mismatches (src/llm_wiki_cli/services/documentation_native.py)"]
    n5["evaluate_documentation_native_freshness (src/llm_wiki_cli/services/documentation_native.py)"]
    n6["_validate_manifest_knowledge_parity (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n7["_validate_surface_knowledge_parity (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n8["_knowledge_counts (src/llm_wiki_cli/services/knowledge_consumption.py)"]
    n9["KnowledgeReadView.knowledge_index (src/llm_wiki_cli/services/knowledge_consumption.py)"]
    n10["_validated_bundle_payload (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n11["_basis_incompatibility_reason (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n12["_evaluate_concept (src/llm_wiki_cli/services/knowledge_freshness.py)"]
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
    n12 --> n0
    click n0 "../modules/knowledge_model.md"
    click n1 "../modules/knowledge_cmd.md"
    click n2 "../modules/knowledge_cmd.md"
    click n3 "../modules/knowledge_cmd.md"
    click n4 "../modules/documentation_native.md"
    click n5 "../modules/documentation_native.md"
    click n6 "../modules/knowledge_artifacts.md"
    click n7 "../modules/knowledge_artifacts.md"
    click n8 "../modules/knowledge_consumption.md"
    click n9 "../modules/knowledge_consumption.md"
    click n10 "../modules/knowledge_envelope.md"
    click n11 "../modules/knowledge_freshness.md"
    click n12 "../modules/knowledge_freshness.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 3 | `bundle`, `concepts`, `extensions`, `relationships`, `schema_version` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_concept_for_uid` | type_reference | [knowledge_cmd](../modules/knowledge_cmd.md) | — |
| `_scope_locator_for_uid` | type_reference | [knowledge_cmd](../modules/knowledge_cmd.md) | — |
| `_status_payload` | type_reference | [knowledge_cmd](../modules/knowledge_cmd.md) | — |
| `_source_mismatches` | type_reference | [documentation_native](../modules/documentation_native.md) | — |
| `evaluate_documentation_native_freshness` | type_reference | [documentation_native](../modules/documentation_native.md) | — |
| `_validate_manifest_knowledge_parity` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `_validate_surface_knowledge_parity` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `_knowledge_counts` | type_reference | [knowledge_consumption](../modules/knowledge_consumption.md) | — |
| `KnowledgeReadView.knowledge_index` | type_reference | [knowledge_consumption](../modules/knowledge_consumption.md) | — |
| `_validated_bundle_payload` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 1 |
| `_basis_incompatibility_reason` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_evaluate_concept` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |

> References: showing 12 of 52 logical references; 40 omitted by the 12-row generated summary limit.
