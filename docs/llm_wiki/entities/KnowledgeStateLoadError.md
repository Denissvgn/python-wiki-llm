# KnowledgeStateLoadError

**Location:** `src/llm_wiki_cli/services/knowledge_loader.py:67`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_loader](../modules/knowledge_loader.md)

## Description

Raised by reject/rebuild policy when no valid state can be returned.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(status: KnowledgeLoadState, issues: tuple[KnowledgeLoadIssue, ...])` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeStateLoadError (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/commands/knowledge_cmd.py"]
    n3["src/llm_wiki_cli/commands/migrate_cmd.py"]
    n4["_knowledge_error_view (src/llm_wiki_cli/services/context_service.py)"]
    n5["src/llm_wiki_cli/services/knowledge_consumption.py"]
    n6["load_knowledge_state (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n7["_snapshot_error_view (src/llm_wiki_cli/services/knowledge_observability.py)"]
    n8["src/llm_wiki_cli/services/lint_service.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/knowledge_loader.md"
    click n2 "../modules/knowledge_cmd.md"
    click n3 "../modules/migrate_cmd.md"
    click n4 "../modules/context_service.md"
    click n5 "../modules/knowledge_consumption.md"
    click n6 "../modules/knowledge_loader.md"
    click n7 "../modules/knowledge_observability.md"
    click n8 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_loader](../modules/knowledge_loader.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `knowledge_cmd` | import | [knowledge_cmd](../modules/knowledge_cmd.md) |
| `migrate_cmd` | import | [migrate_cmd](../modules/migrate_cmd.md) |
| `_knowledge_error_view` | type_reference | [context_service](../modules/context_service.md) |
| `knowledge_consumption` | import | [knowledge_consumption](../modules/knowledge_consumption.md) |
| `load_knowledge_state` | call | [knowledge_loader](../modules/knowledge_loader.md) |
| `load_knowledge_state` | call | [knowledge_loader](../modules/knowledge_loader.md) |
| `_snapshot_error_view` | type_reference | [knowledge_observability](../modules/knowledge_observability.md) |
| `lint_service` | import | [lint_service](../modules/lint_service.md) |
