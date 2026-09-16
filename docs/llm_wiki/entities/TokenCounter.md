# TokenCounter

**Location:** `src/llm_wiki_cli/services/token_counting.py:10`
**Kind:** Class
**Bases:** `Protocol`
**Module:** [token_counting](../modules/token_counting.md)

## Description

_Auto-generated from `TokenCounter` in `src/llm_wiki_cli/services/token_counting.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `identity` | `str` | *required* | — |
| `exact` | `bool` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `count` | `(text: str) -> int` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["TokenCounter (src/llm_wiki_cli/services/token_counting.py)"]
    n1["Protocol"]
    n2["apply_task_delta (src/llm_wiki_cli/api.py)"]
    n3["build_budgeted_context (src/llm_wiki_cli/api.py)"]
    n4["build_task_context (src/llm_wiki_cli/api.py)"]
    n5["open_context_session (src/llm_wiki_cli/api.py)"]
    n6["reconcile_task_context (src/llm_wiki_cli/api.py)"]
    n7["validate_budgeted_context (src/llm_wiki_cli/api.py)"]
    n8["validate_task_context (src/llm_wiki_cli/api.py)"]
    n9["build_budgeted_context (src/llm_wiki_cli/services/context_budget.py)"]
    n10["validate_budgeted_context (src/llm_wiki_cli/services/context_budget.py)"]
    n11["McpWikiService.__init__ (src/llm_wiki_cli/services/mcp_server.py)"]
    n12["build_task_read (src/llm_wiki_cli/services/task_context.py)"]
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
    n12 --> n0
    click n0 "../modules/token_counting.md"
    click n2 "../modules/api.md"
    click n3 "../modules/api.md"
    click n4 "../modules/api.md"
    click n5 "../modules/api.md"
    click n6 "../modules/api.md"
    click n7 "../modules/api.md"
    click n8 "../modules/api.md"
    click n9 "../modules/context_budget.md"
    click n10 "../modules/context_budget.md"
    click n11 "../modules/mcp_server.md"
    click n12 "../modules/task_context.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [token_counting](../modules/token_counting.md) | 1 | `exact`, `identity` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Protocol` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `apply_task_delta` | type_reference | [api](../modules/api.md) | — |
| `build_budgeted_context` | type_reference | [api](../modules/api.md) | — |
| `build_task_context` | type_reference | [api](../modules/api.md) | — |
| `open_context_session` | type_reference | [api](../modules/api.md) | — |
| `reconcile_task_context` | type_reference | [api](../modules/api.md) | — |
| `validate_budgeted_context` | type_reference | [api](../modules/api.md) | — |
| `validate_task_context` | type_reference | [api](../modules/api.md) | — |
| `build_budgeted_context` | type_reference | [context_budget](../modules/context_budget.md) | — |
| `validate_budgeted_context` | type_reference | [context_budget](../modules/context_budget.md) | — |
| `McpWikiService.__init__` | type_reference | [mcp_server](../modules/mcp_server.md) | — |
| `build_task_read` | type_reference | [task_context](../modules/task_context.md) | — |
