# TokenCounter

**Location:** `src/llm_wiki_engine/token_counters.py:13`
**Kind:** Class
**Bases:** `Protocol`
**Module:** [token_counters](../modules/token_counters.md)

## Description

_Auto-generated from `TokenCounter` in `src/llm_wiki_engine/token_counters.py`._

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
    n0["TokenCounter (src/llm_wiki_engine/token_counters.py)"]
    n1["Protocol"]
    n2["build_task_read (src/llm_wiki_cli/services/task_context.py)"]
    n3["src/llm_wiki_cli/services/token_counting.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/token_counters.md"
    click n2 "../modules/task_context.md"
    click n3 "../modules/token_counting.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [token_counters](../modules/token_counters.md) | 1 | `exact`, `identity` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Protocol` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `build_task_read` | type_reference | [task_context](../modules/task_context.md) | — |
| `token_counting` | import | [token_counting](../modules/token_counting.md) | — |
