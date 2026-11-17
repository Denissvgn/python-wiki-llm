# KnowledgeStateLoadError

**Location:** `src/llm_wiki_cli/services/knowledge_loader.py:73`
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
    n2["src/llm_wiki_cli/api.py"]
    n3["src/llm_wiki_cli/commands/knowledge_cmd.py"]
    n4["_build_context_knowledge_view (src/llm_wiki_cli/services/context_service.py)"]
    n5["_knowledge_error_view (src/llm_wiki_cli/services/context_service.py)"]
    n6["src/llm_wiki_cli/services/knowledge_consumption.py"]
    n7["load_knowledge_state (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n8["_snapshot_error_view (src/llm_wiki_cli/services/knowledge_observability.py)"]
    n9["src/llm_wiki_cli/services/lint_service.py"]
    n10["src/llm_wiki_cli/services/migrate_runtime.py"]
    n11["src/llm_wiki_cli/services/task_context.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    click n0 "../modules/knowledge_loader.md"
    click n2 "../modules/api.md"
    click n3 "../modules/knowledge_cmd.md"
    click n4 "../modules/context_service.md"
    click n5 "../modules/context_service.md"
    click n6 "../modules/knowledge_consumption.md"
    click n7 "../modules/knowledge_loader.md"
    click n8 "../modules/knowledge_observability.md"
    click n9 "../modules/lint_service.md"
    click n10 "../modules/migrate_runtime.md"
    click n11 "../modules/task_context.md"
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

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `knowledge_cmd` | import | [knowledge_cmd](../modules/knowledge_cmd.md) | — |
| `_build_context_knowledge_view` | call | [context_service](../modules/context_service.md) | 1 |
| `_knowledge_error_view` | type_reference | [context_service](../modules/context_service.md) | — |
| `knowledge_consumption` | import | [knowledge_consumption](../modules/knowledge_consumption.md) | — |
| `load_knowledge_state` | call | [knowledge_loader](../modules/knowledge_loader.md) | 2 |
| `_snapshot_error_view` | type_reference | [knowledge_observability](../modules/knowledge_observability.md) | — |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
| `migrate_runtime` | import | [migrate_runtime](../modules/migrate_runtime.md) | — |
| `task_context` | import | [task_context](../modules/task_context.md) | — |
