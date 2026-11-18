# ConceptRecord

**Location:** `src/llm_wiki_engine/knowledge_model.py:398`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_model](../modules/knowledge_model.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `ConceptRecord` in `src/llm_wiki_engine/knowledge_model.py`._

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

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ConceptRecord (src/llm_wiki_engine/knowledge_model.py)"]
    n1["captured_evidence_diagnostic (src/llm_wiki_cli/services/evidence_diagnostics.py)"]
    n2["_endpoint_concept (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n3["_governance_summary (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n4["_project_concept (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n5["_project_endpoint (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n6["_project_freshness (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n7["_project_machine_check (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n8["_project_relation (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n9["_project_relationships (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n10["_evaluate_concept (src/llm_wiki_engine/knowledge_freshness.py)"]
    n11["_reliable_recorded_basis (src/llm_wiki_engine/knowledge_freshness.py)"]
    n12["structural_freshness_modeled (src/llm_wiki_engine/knowledge_freshness.py)"]
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
    click n1 "../modules/evidence_diagnostics.md"
    click n2 "../modules/knowledge_projection.md"
    click n3 "../modules/knowledge_projection.md"
    click n4 "../modules/knowledge_projection.md"
    click n5 "../modules/knowledge_projection.md"
    click n6 "../modules/knowledge_projection.md"
    click n7 "../modules/knowledge_projection.md"
    click n8 "../modules/knowledge_projection.md"
    click n9 "../modules/knowledge_projection.md"
    click n10 "../modules/knowledge_freshness.md"
    click n11 "../modules/knowledge_freshness.md"
    click n12 "../modules/knowledge_freshness.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `concept_kind`, `document`, `extensions`, `facets`, `lifecycle`, `locator`, `title` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `captured_evidence_diagnostic` | type_reference | [evidence_diagnostics](../modules/evidence_diagnostics.md) | — |
| `_endpoint_concept` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_governance_summary` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_concept` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_endpoint` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_freshness` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_machine_check` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_relation` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_relationships` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_evaluate_concept` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_reliable_recorded_basis` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `structural_freshness_modeled` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |

> References: showing 12 of 25 logical references; 13 omitted by the 12-row generated summary limit.
