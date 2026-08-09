# EvidenceState

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:125`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

_Auto-generated from `EvidenceState` in `src/llm_wiki_cli/services/knowledge_model.py`._

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `UNKNOWN` | `'unknown'` | — |
| `PRESENT` | `'present'` | — |
| `MISSING` | `'missing'` | — |
| `INVALID` | `'invalid'` | — |
| `NOT_APPLICABLE` | `'not-applicable'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["EvidenceState (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/context_service.py"]
    n4["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n5["src/llm_wiki_cli/services/knowledge_consumption.py"]
    n6["src/llm_wiki_cli/services/knowledge_freshness.py"]
    n7["src/llm_wiki_cli/services/knowledge_governance.py"]
    n8["_require_structure_state (src/llm_wiki_cli/services/knowledge_index.py)"]
    n9["src/llm_wiki_cli/services/knowledge_observability.py"]
    n10["src/llm_wiki_cli/services/knowledge_projection.py"]
    n11["src/llm_wiki_cli/services/lint_service.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    click n0 "../modules/knowledge_model.md"
    click n3 "../modules/context_service.md"
    click n4 "../modules/knowledge_artifacts.md"
    click n5 "../modules/knowledge_consumption.md"
    click n6 "../modules/knowledge_freshness.md"
    click n7 "../modules/knowledge_governance.md"
    click n8 "../modules/knowledge_index.md"
    click n9 "../modules/knowledge_observability.md"
    click n10 "../modules/knowledge_projection.md"
    click n11 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `INVALID`, `MISSING`, `NOT_APPLICABLE`, `PRESENT`, `UNKNOWN` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `context_service` | import | [context_service](../modules/context_service.md) |
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `knowledge_consumption` | import | [knowledge_consumption](../modules/knowledge_consumption.md) |
| `knowledge_freshness` | import | [knowledge_freshness](../modules/knowledge_freshness.md) |
| `knowledge_governance` | import | [knowledge_governance](../modules/knowledge_governance.md) |
| `_require_structure_state` | type_reference | [knowledge_index](../modules/knowledge_index.md) |
| `knowledge_observability` | import | [knowledge_observability](../modules/knowledge_observability.md) |
| `knowledge_projection` | import | [knowledge_projection](../modules/knowledge_projection.md) |
| `lint_service` | import | [lint_service](../modules/lint_service.md) |
