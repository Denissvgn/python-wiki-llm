# ObservationScope

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:220`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

_Auto-generated from `ObservationScope` in `src/llm_wiki_cli/services/knowledge_model.py`._

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `UNKNOWN` | `'unknown'` | — |
| `MODULE` | `'module'` | — |
| `ENTITY` | `'entity'` | — |
| `INFRASTRUCTURE` | `'infrastructure'` | — |
| `AGGREGATE` | `'aggregate'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ObservationScope (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/documentation_native.py"]
    n4["_live_basis_details (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n5["_evidence_basis (src/llm_wiki_cli/services/knowledge_index.py)"]
    n6["src/llm_wiki_cli/services/knowledge_orchestration.py"]
    n7["src/llm_wiki_cli/services/knowledge_projection.py"]
    n8["_promised_evidence_reason (src/llm_wiki_cli/services/lint_service.py)"]
    n9["_promised_structural_scope (src/llm_wiki_cli/services/lint_service.py)"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/knowledge_model.md"
    click n3 "../modules/documentation_native.md"
    click n4 "../modules/knowledge_freshness.md"
    click n5 "../modules/knowledge_index.md"
    click n6 "../modules/knowledge_orchestration.md"
    click n7 "../modules/knowledge_projection.md"
    click n8 "../modules/lint_service.md"
    click n9 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `AGGREGATE`, `ENTITY`, `INFRASTRUCTURE`, `MODULE`, `UNKNOWN` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `documentation_native` | import | [documentation_native](../modules/documentation_native.md) |
| `_live_basis_details` | call | [knowledge_freshness](../modules/knowledge_freshness.md) |
| `_evidence_basis` | call | [knowledge_index](../modules/knowledge_index.md) |
| `knowledge_orchestration` | import | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| `knowledge_projection` | import | [knowledge_projection](../modules/knowledge_projection.md) |
| `_promised_evidence_reason` | type_reference | [lint_service](../modules/lint_service.md) |
| `_promised_structural_scope` | type_reference | [lint_service](../modules/lint_service.md) |
