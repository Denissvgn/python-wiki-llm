# _JoinedPage

**Location:** `src/llm_wiki_cli/services/knowledge_index.py:174`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_index](../modules/knowledge_index.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_JoinedPage` in `src/llm_wiki_cli/services/knowledge_index.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `page` | `WikiSurfacePage` | *required* | — |
| `surface` | `_SurfacePage` | *required* | — |
| `content` | `str` | *required* | — |
| `page_hash` | `str` | *required* | — |
| `mapping` | `ManifestPageSource \| None` | *required* | — |
| `baseline` | `ManifestEvidenceBaseline \| None` | *required* | — |
| `tombstone` | `ManifestTombstone \| None` | *required* | — |
| `infrastructure_basis` | `ConceptObservationBasis \| None` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `basis` | `() -> ConceptObservationBasis \| None` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_JoinedPage (src/llm_wiki_cli/services/knowledge_index.py)"]
    n1["_concept_for_page (src/llm_wiki_cli/services/knowledge_index.py)"]
    n2["_derived_relationship (src/llm_wiki_cli/services/knowledge_index.py)"]
    n3["_link_relationship (src/llm_wiki_cli/services/knowledge_index.py)"]
    n4["_structural_facet (src/llm_wiki_cli/services/knowledge_index.py)"]
    n5["_validate_and_join_inputs (src/llm_wiki_cli/services/knowledge_index.py)"]
    n6["_validate_observation_endpoint (src/llm_wiki_cli/services/knowledge_index.py)"]
    n7["_validate_page_evidence (src/llm_wiki_cli/services/knowledge_index.py)"]
    n8["_validated_observations (src/llm_wiki_cli/services/knowledge_index.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/knowledge_index.md"
    click n1 "../modules/knowledge_index.md"
    click n2 "../modules/knowledge_index.md"
    click n3 "../modules/knowledge_index.md"
    click n4 "../modules/knowledge_index.md"
    click n5 "../modules/knowledge_index.md"
    click n6 "../modules/knowledge_index.md"
    click n7 "../modules/knowledge_index.md"
    click n8 "../modules/knowledge_index.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_index](../modules/knowledge_index.md) | 1 | `baseline`, `content`, `infrastructure_basis`, `mapping`, `page`, `page_hash`, `surface`, `tombstone` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_concept_for_page` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_derived_relationship` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_link_relationship` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_structural_facet` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_validate_and_join_inputs` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
| `_validate_observation_endpoint` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_validate_page_evidence` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_validated_observations` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
