# EstimatedCounter

**Location:** `src/llm_wiki_engine/token_counters.py:20`
**Kind:** Class
**Bases:** —
**Module:** [token_counters](../modules/token_counters.md)

## Description

_Auto-generated from `EstimatedCounter` in `src/llm_wiki_engine/token_counters.py`._

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `count` | `(text: str) -> int` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["EstimatedCounter (src/llm_wiki_engine/token_counters.py)"]
    n1["build_budgeted_context (src/llm_wiki_cli/services/context_budget.py)"]
    n2["_counter (src/llm_wiki_cli/services/task_context.py)"]
    n3["src/llm_wiki_cli/services/token_counting.py"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/token_counters.md"
    click n1 "../modules/context_budget.md"
    click n2 "../modules/task_context.md"
    click n3 "../modules/token_counting.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [token_counters](../modules/token_counters.md) | 1 | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `build_budgeted_context` | call | [context_budget](../modules/context_budget.md) | 1 |
| `_counter` | call | [task_context](../modules/task_context.md) | 1 |
| `token_counting` | import | [token_counting](../modules/token_counting.md) | — |
