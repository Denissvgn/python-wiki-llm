# KnowledgeMismatchPolicy

**Location:** `src/llm_wiki_cli/services/knowledge_loader.py:36`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_loader](../modules/knowledge_loader.md)

## Description

Caller-selected behavior when a present artifact set is not valid.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `REJECT` | `'reject'` | — |
| `REBUILD` | `'rebuild'` | — |
| `DEGRADED` | `'degraded'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeMismatchPolicy (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/commands/knowledge_cmd.py"]
    n4["src/llm_wiki_cli/services/context_service.py"]
    n5["src/llm_wiki_cli/services/knowledge_consumption.py"]
    n6["load_knowledge_state (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n7["src/llm_wiki_cli/services/knowledge_observability.py"]
    n8["src/llm_wiki_cli/services/lint_service.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/knowledge_loader.md"
    click n3 "../modules/knowledge_cmd.md"
    click n4 "../modules/context_service.md"
    click n5 "../modules/knowledge_consumption.md"
    click n6 "../modules/knowledge_loader.md"
    click n7 "../modules/knowledge_observability.md"
    click n8 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_loader](../modules/knowledge_loader.md) | 0 | `DEGRADED`, `REBUILD`, `REJECT` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_cmd` | import | [knowledge_cmd](../modules/knowledge_cmd.md) | — |
| `context_service` | import | [context_service](../modules/context_service.md) | — |
| `knowledge_consumption` | import | [knowledge_consumption](../modules/knowledge_consumption.md) | — |
| `load_knowledge_state` | call | [knowledge_loader](../modules/knowledge_loader.md) | 1 |
| `load_knowledge_state` | type_reference | [knowledge_loader](../modules/knowledge_loader.md) | — |
| `knowledge_observability` | import | [knowledge_observability](../modules/knowledge_observability.md) | — |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
