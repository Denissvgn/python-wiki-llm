# EvidenceState

**Location:** `src/llm_wiki_engine/knowledge_model.py:152`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

_Auto-generated from `EvidenceState` in `src/llm_wiki_engine/knowledge_model.py`._

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `UNKNOWN` | `'unknown'` | — |
| `PRESENT` | `'present'` | — |
| `MISSING` | `'missing'` | — |
| `INVALID` | `'invalid'` | — |
| `NOT_APPLICABLE` | `'not-applicable'` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["EvidenceState (src/llm_wiki_engine/knowledge_model.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/context_service.py"]
    n4["src/llm_wiki_cli/services/evidence_diagnostics.py"]
    n5["src/llm_wiki_cli/services/knowledge_projection.py"]
    n6["src/llm_wiki_cli/services/lint_service.py"]
    n7["src/llm_wiki_engine/context_packet.py"]
    n8["src/llm_wiki_engine/context_request_format.py"]
    n9["src/llm_wiki_engine/knowledge_artifacts.py"]
    n10["src/llm_wiki_engine/knowledge_consumption.py"]
    n11["src/llm_wiki_engine/knowledge_freshness.py"]
    n12["src/llm_wiki_engine/knowledge_governance.py"]
    n13["_require_structure_state (src/llm_wiki_engine/knowledge_index.py)"]
    n14["src/llm_wiki_engine/knowledge_kinds.py"]
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
    n12 --> n0
    n13 --> n0
    n14 --> n0
    click n0 "../modules/knowledge_model.md"
    click n3 "../modules/context_service.md"
    click n4 "../modules/evidence_diagnostics.md"
    click n5 "../modules/knowledge_projection.md"
    click n6 "../modules/lint_service.md"
    click n7 "../modules/context_packet.md"
    click n8 "../modules/context_request_format.md"
    click n9 "../modules/knowledge_artifacts.md"
    click n10 "../modules/knowledge_consumption.md"
    click n11 "../modules/knowledge_freshness.md"
    click n12 "../modules/knowledge_governance.md"
    click n13 "../modules/knowledge_index.md"
    click n14 "../modules/knowledge_kinds.md"
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

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `context_service` | import | [context_service](../modules/context_service.md) | — |
| `evidence_diagnostics` | import | [evidence_diagnostics](../modules/evidence_diagnostics.md) | — |
| `knowledge_projection` | import | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
| `context_packet` | import | [context_packet](../modules/context_packet.md) | — |
| `context_request_format` | import | [context_request_format](../modules/context_request_format.md) | — |
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `knowledge_consumption` | import | [knowledge_consumption](../modules/knowledge_consumption.md) | — |
| `knowledge_freshness` | import | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `knowledge_governance` | import | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `_require_structure_state` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `knowledge_kinds` | import | [knowledge_kinds](../modules/knowledge_kinds.md) | — |

> References: showing 12 of 14 logical references; 2 omitted by the 12-row generated summary limit.
