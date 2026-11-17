# _Discard

**Location:** `src/llm_wiki_cli/services/host.py:237`
**Kind:** Class
**Bases:** `io.TextIOBase`
**Module:** [host](../modules/host.md)

## Description

_Auto-generated from `_Discard` in `src/llm_wiki_cli/services/host.py`._

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `writable` | `() -> bool` | — | — |
| `write` | `(text: str) -> int` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_Discard (src/llm_wiki_cli/services/host.py)"]
    n1["io.TextIOBase"]
    n2["discarding_output (src/llm_wiki_cli/services/host.py)"]
    n3["discarding_stdout (src/llm_wiki_cli/services/host.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/host.md"
    click n2 "../modules/host.md"
    click n3 "../modules/host.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [host](../modules/host.md) | 2 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `io.TextIOBase` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `discarding_output` | call | [host](../modules/host.md) | 1 |
| `discarding_stdout` | call | [host](../modules/host.md) | 1 |
