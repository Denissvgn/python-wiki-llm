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
    n2["build_budgeted_context (src/llm_wiki_cli/api.py)"]
    n3["build_budgeted_context (src/llm_wiki_cli/services/context_budget.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/token_counting.md"
    click n2 "../modules/api.md"
    click n3 "../modules/context_budget.md"
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
| `build_budgeted_context` | type_reference | [api](../modules/api.md) | — |
| `build_budgeted_context` | type_reference | [context_budget](../modules/context_budget.md) | — |
