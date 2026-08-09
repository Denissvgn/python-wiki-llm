# ComputedFreshness

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:170`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

Live comparison outcomes; never serialized in the knowledge index.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `UNKNOWN` | `'unknown'` | — |
| `CURRENT` | `'current'` | — |
| `NONSEMANTIC_SOURCE_CHANGE` | `'nonsemantic-source-change'` | — |
| `SOURCE_CHANGED` | `'source-changed'` | — |
| `BASIS_INCOMPATIBLE` | `'basis-incompatible'` | — |
| `SOURCE_MISSING` | `'source-missing'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ComputedFreshness (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/context_packet.py"]
    n4["src/llm_wiki_cli/services/context_service.py"]
    n5["src/llm_wiki_cli/services/doctor_service.py"]
    n6["src/llm_wiki_cli/services/documentation_native.py"]
    n7["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n8["src/llm_wiki_cli/services/knowledge_consumption.py"]
    n9["_result (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n10["knowledge_freshness_hint (src/llm_wiki_cli/services/knowledge_observability.py)"]
    n11["src/llm_wiki_cli/services/knowledge_projection.py"]
    n12["src/llm_wiki_cli/services/lint_service.py"]
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
    click n0 "../modules/knowledge_model.md"
    click n3 "../modules/context_packet.md"
    click n4 "../modules/context_service.md"
    click n5 "../modules/doctor_service.md"
    click n6 "../modules/documentation_native.md"
    click n7 "../modules/documentation_wiki_input.md"
    click n8 "../modules/knowledge_consumption.md"
    click n9 "../modules/knowledge_freshness.md"
    click n10 "../modules/knowledge_observability.md"
    click n11 "../modules/knowledge_projection.md"
    click n12 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `BASIS_INCOMPATIBLE`, `CURRENT`, `NONSEMANTIC_SOURCE_CHANGE`, `SOURCE_CHANGED`, `SOURCE_MISSING`, `UNKNOWN` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `context_packet` | import | [context_packet](../modules/context_packet.md) |
| `context_service` | import | [context_service](../modules/context_service.md) |
| `doctor_service` | import | [doctor_service](../modules/doctor_service.md) |
| `documentation_native` | import | [documentation_native](../modules/documentation_native.md) |
| `documentation_wiki_input` | import | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `knowledge_consumption` | import | [knowledge_consumption](../modules/knowledge_consumption.md) |
| `_result` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) |
| `knowledge_freshness_hint` | type_reference | [knowledge_observability](../modules/knowledge_observability.md) |
| `knowledge_projection` | import | [knowledge_projection](../modules/knowledge_projection.md) |
| `lint_service` | import | [lint_service](../modules/lint_service.md) |
