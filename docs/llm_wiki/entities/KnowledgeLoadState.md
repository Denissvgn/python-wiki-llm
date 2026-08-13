# KnowledgeLoadState

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:181`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

Validated artifact-load outcomes; never persisted in the knowledge index.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `VALID` | `'valid'` | — |
| `ABSENT` | `'absent'` | — |
| `INVALID` | `'invalid'` | — |
| `MIXED_SNAPSHOT` | `'mixed-snapshot'` | — |
| `DEGRADED` | `'degraded'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeLoadState (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/commands/knowledge_cmd.py"]
    n4["src/llm_wiki_cli/services/context_service.py"]
    n5["src/llm_wiki_cli/services/doctor_service.py"]
    n6["src/llm_wiki_cli/services/knowledge_consumption.py"]
    n7["_live_governance_issues (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n8["KnowledgeStateLoadError.__init__ (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n9["src/llm_wiki_cli/services/knowledge_observability.py"]
    n10["src/llm_wiki_cli/services/lint_service.py"]
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
    click n0 "../modules/knowledge_model.md"
    click n3 "../modules/knowledge_cmd.md"
    click n4 "../modules/context_service.md"
    click n5 "../modules/doctor_service.md"
    click n6 "../modules/knowledge_consumption.md"
    click n7 "../modules/knowledge_loader.md"
    click n8 "../modules/knowledge_loader.md"
    click n9 "../modules/knowledge_observability.md"
    click n10 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `ABSENT`, `DEGRADED`, `INVALID`, `MIXED_SNAPSHOT`, `VALID` |

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
| `doctor_service` | import | [doctor_service](../modules/doctor_service.md) | — |
| `knowledge_consumption` | import | [knowledge_consumption](../modules/knowledge_consumption.md) | — |
| `_live_governance_issues` | type_reference | [knowledge_loader](../modules/knowledge_loader.md) | — |
| `KnowledgeStateLoadError.__init__` | type_reference | [knowledge_loader](../modules/knowledge_loader.md) | — |
| `knowledge_observability` | import | [knowledge_observability](../modules/knowledge_observability.md) | — |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
