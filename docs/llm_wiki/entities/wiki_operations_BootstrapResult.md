# BootstrapResult

**Location:** `src/llm_wiki_engine/wiki_operations.py:68`
**Kind:** Class
**Bases:** —
**Module:** [wiki_operations](../modules/wiki_operations.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `BootstrapResult` in `src/llm_wiki_engine/wiki_operations.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `sources` | `int` | *required* | — |
| `pages` | `tuple[str, ...]` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `to_dict` | `() -> dict[str, Any]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["BootstrapResult (src/llm_wiki_engine/wiki_operations.py)"]
    n1["Engine.bootstrap (src/llm_wiki_engine/engine.py)"]
    n2["bootstrap (src/llm_wiki_engine/wiki_operations.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/wiki_operations.md"
    click n1 "../modules/engine.md"
    click n2 "../modules/wiki_operations.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [wiki_operations](../modules/wiki_operations.md) | 1 | `pages`, `sources` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `Engine.bootstrap` | type_reference | [engine](../modules/engine.md) | — |
| `bootstrap` | call | [wiki_operations](../modules/wiki_operations.md) | 1 |
| `bootstrap` | type_reference | [wiki_operations](../modules/wiki_operations.md) | — |
