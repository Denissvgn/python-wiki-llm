# TokenCounter

**Location:** `src/llm_wiki_cli/services/token_counting.py:11`
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
    n4["build_compact_task_context (src/llm_wiki_cli/api.py)"]
    n5["build_task_context (src/llm_wiki_cli/api.py)"]
    n6["expand_compact_task_context (src/llm_wiki_cli/api.py)"]
    n7["open_context_session (src/llm_wiki_cli/api.py)"]
    n8["reconcile_task_context (src/llm_wiki_cli/api.py)"]
    n9["render_compact_task_context (src/llm_wiki_cli/api.py)"]
    n10["validate_budgeted_context (src/llm_wiki_cli/api.py)"]
    n11["validate_compact_task_context (src/llm_wiki_cli/api.py)"]
    n12["validate_task_context (src/llm_wiki_cli/api.py)"]
    n13["build_budgeted_context (src/llm_wiki_cli/services/context_budget.py)"]
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
    n13 --> n0
    click n0 "../modules/token_counting.md"
    click n2 "../modules/api.md"
    click n3 "../modules/api.md"
    click n4 "../modules/api.md"
    click n5 "../modules/api.md"
    click n6 "../modules/api.md"
    click n7 "../modules/api.md"
    click n8 "../modules/api.md"
    click n9 "../modules/api.md"
    click n10 "../modules/api.md"
    click n11 "../modules/api.md"
    click n12 "../modules/api.md"
    click n13 "../modules/context_budget.md"
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
| `build_compact_task_context` | type_reference | [api](../modules/api.md) | — |
| `build_task_context` | type_reference | [api](../modules/api.md) | — |
| `expand_compact_task_context` | type_reference | [api](../modules/api.md) | — |
| `open_context_session` | type_reference | [api](../modules/api.md) | — |
| `reconcile_task_context` | type_reference | [api](../modules/api.md) | — |
| `render_compact_task_context` | type_reference | [api](../modules/api.md) | — |
| `validate_budgeted_context` | type_reference | [api](../modules/api.md) | — |
| `validate_compact_task_context` | type_reference | [api](../modules/api.md) | — |
| `validate_task_context` | type_reference | [api](../modules/api.md) | — |
| `build_budgeted_context` | type_reference | [context_budget](../modules/context_budget.md) | — |

> References: showing 12 of 15 logical references; 3 omitted by the 12-row generated summary limit.
