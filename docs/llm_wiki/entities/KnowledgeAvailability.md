# KnowledgeAvailability

**Location:** `src/llm_wiki_cli/services/knowledge_consumption.py:42`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_consumption](../modules/knowledge_consumption.md)

## Description

Knowledge capability available to every native read consumer.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `READY` | `'ready'` | — |
| `ABSENT` | `'absent'` | — |
| `DEGRADED` | `'degraded'` | — |
| `UNSUPPORTED` | `'unsupported'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeAvailability (src/llm_wiki_cli/services/knowledge_consumption.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/context_service.py"]
    n4["src/llm_wiki_cli/services/doctor_service.py"]
    n5["src/llm_wiki_cli/services/documentation_queries.py"]
    n6["KnowledgeAggregateSummary.__post_init__ (src/llm_wiki_cli/services/knowledge_observability.py)"]
    n7["src/llm_wiki_cli/services/knowledge_projection.py"]
    n8["src/llm_wiki_cli/services/lint_service.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/knowledge_consumption.md"
    click n3 "../modules/context_service.md"
    click n4 "../modules/doctor_service.md"
    click n5 "../modules/documentation_queries.md"
    click n6 "../modules/knowledge_observability.md"
    click n7 "../modules/knowledge_projection.md"
    click n8 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_consumption](../modules/knowledge_consumption.md) | 0 | `ABSENT`, `DEGRADED`, `READY`, `UNSUPPORTED` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `context_service` | import | [context_service](../modules/context_service.md) | — |
| `doctor_service` | import | [doctor_service](../modules/doctor_service.md) | — |
| `documentation_queries` | import | [documentation_queries](../modules/documentation_queries.md) | — |
| `KnowledgeAggregateSummary.__post_init__` | call | [knowledge_observability](../modules/knowledge_observability.md) | 1 |
| `knowledge_projection` | import | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
