# ConceptFreshnessBasis

**Location:** `src/llm_wiki_cli/services/knowledge_freshness.py:198`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_freshness](../modules/knowledge_freshness.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Normalized recorded or live concept basis returned to consumers.

A live basis may carry fresh normalization detail through the in-memory
comparison to evidence explanation. Recorded basis construction does not invent
that detail. The established serialized basis fields stay unchanged; bounded
versioned diagnostics travel in the existing explanation text. Diagnostic presence
does not establish compatible evidence, freshness or a committed repair.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `scope` | `ObservationScope` | *required* | — |
| `source_path` | `str` | *required* | — |
| `extractor_ref` | `str` | *required* | — |
| `source_content_hash` | `str` | *required* | — |
| `concept_observation_hash` | `str \| None` | *required* | — |
| `analysis_basis_hash` | `str \| None` | *required* | — |
| `unknown_reason` | `str \| None` | `None` | — |
| `normalization_diagnostic` | `NormalizationDiagnostic \| None` | `field(default=None, repr=False, compare=False)` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ConceptFreshnessBasis (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n1["_live_basis_details (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n2["_recorded_basis_details (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n3["_result (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/knowledge_freshness.md"
    click n1 "../modules/knowledge_freshness.md"
    click n2 "../modules/knowledge_freshness.md"
    click n3 "../modules/knowledge_freshness.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_freshness](../modules/knowledge_freshness.md) | 0 | `analysis_basis_hash`, `concept_observation_hash`, `extractor_ref`, `normalization_diagnostic`, `scope`, `source_content_hash`, `source_path`, `unknown_reason` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_live_basis_details` | call | [knowledge_freshness](../modules/knowledge_freshness.md) | 1 |
| `_live_basis_details` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_recorded_basis_details` | call | [knowledge_freshness](../modules/knowledge_freshness.md) | 1 |
| `_recorded_basis_details` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_result` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
