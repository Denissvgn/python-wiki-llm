# KnowledgeIndex

**Location:** `src/llm_wiki_engine/knowledge_model.py:477`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_model](../modules/knowledge_model.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `KnowledgeIndex` in `src/llm_wiki_engine/knowledge_model.py`._

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
    n0["KnowledgeIndex (src/llm_wiki_engine/knowledge_model.py)"]
    n1["_concept_for_uid (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n2["_scope_locator_for_uid (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n3["_status_payload (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n4["_source_mismatches (src/llm_wiki_cli/services/documentation_native.py)"]
    n5["evaluate_documentation_native_freshness (src/llm_wiki_cli/services/documentation_native.py)"]
    n6["_runtime_live_concept_bases (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n7["_approved_public_repository_identity (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n8["_initial_omitted_counts (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n9["_project_bundle (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n10["_project_producer (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n11["_project_relationships (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n12["_unknown_extension_count (src/llm_wiki_cli/services/knowledge_projection.py)"]
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
    click n6 "../modules/knowledge_orchestration.md"
    click n7 "../modules/knowledge_projection.md"
    click n8 "../modules/knowledge_projection.md"
    click n9 "../modules/knowledge_projection.md"
    click n10 "../modules/knowledge_projection.md"
    click n11 "../modules/knowledge_projection.md"
    click n12 "../modules/knowledge_projection.md"
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
| `_runtime_live_concept_bases` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `_approved_public_repository_identity` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_initial_omitted_counts` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_bundle` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_producer` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_relationships` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_unknown_extension_count` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |

> References: showing 12 of 64 logical references; 52 omitted by the 12-row generated summary limit.
