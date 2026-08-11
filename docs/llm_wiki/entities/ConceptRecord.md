# ConceptRecord

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:371`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_model](../modules/knowledge_model.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `ConceptRecord` in `src/llm_wiki_cli/services/knowledge_model.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `locator` | `str` | *required* | — |
| `concept_kind` | `ConceptKindValue` | *required* | — |
| `title` | `str` | *required* | — |
| `document` | `DocumentRecord` | *required* | — |
| `facets` | `ConceptFacets` | *required* | — |
| `lifecycle` | `Lifecycle` | `Lifecycle.UNKNOWN` | — |
| `extensions` | `Extensions` | `field(default_factory=dict)` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ConceptRecord (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["_evaluate_concept (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n2["_reliable_recorded_basis (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n3["_add_supersession_edges (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n4["current_review_evidence (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n5["_concept_for_page (src/llm_wiki_cli/services/knowledge_index.py)"]
    n6["_validate_builder_derived (src/llm_wiki_cli/services/knowledge_index.py)"]
    n7["_validate_builder_link (src/llm_wiki_cli/services/knowledge_index.py)"]
    n8["_concept_to_payload (src/llm_wiki_cli/services/knowledge_model.py)"]
    n9["_parse_concept (src/llm_wiki_cli/services/knowledge_model.py)"]
    n10["_validate_index_references (src/llm_wiki_cli/services/knowledge_model.py)"]
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
    click n0 "../modules/knowledge_model.md"
    click n1 "../modules/knowledge_freshness.md"
    click n2 "../modules/knowledge_freshness.md"
    click n3 "../modules/knowledge_governance.md"
    click n4 "../modules/knowledge_governance.md"
    click n5 "../modules/knowledge_index.md"
    click n6 "../modules/knowledge_index.md"
    click n7 "../modules/knowledge_index.md"
    click n8 "../modules/knowledge_model.md"
    click n9 "../modules/knowledge_model.md"
    click n10 "../modules/knowledge_model.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `concept_kind`, `document`, `extensions`, `facets`, `lifecycle`, `locator`, `title` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_evaluate_concept` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_reliable_recorded_basis` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_add_supersession_edges` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `current_review_evidence` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `_concept_for_page` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
| `_concept_for_page` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_validate_builder_derived` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_validate_builder_link` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_concept_to_payload` | type_reference | [knowledge_model](../modules/knowledge_model.md) | — |
| `_parse_concept` | call | [knowledge_model](../modules/knowledge_model.md) | 1 |
| `_parse_concept` | type_reference | [knowledge_model](../modules/knowledge_model.md) | — |
| `_validate_index_references` | type_reference | [knowledge_model](../modules/knowledge_model.md) | — |

> References: showing 12 of 21 logical references; 9 omitted by the 12-row generated summary limit.
