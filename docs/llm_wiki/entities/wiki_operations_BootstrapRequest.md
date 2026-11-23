# BootstrapRequest

**Location:** `src/llm_wiki_engine/wiki_operations.py:44`
**Kind:** Class
**Bases:** —
**Module:** [wiki_operations](../modules/wiki_operations.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Create a wiki at ``wiki_root`` from the sources under ``source_root``.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `source_root` | `str \| os.PathLike[str]` | *required* | — |
| `wiki_root` | `str \| os.PathLike[str]` | *required* | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["BootstrapRequest (src/llm_wiki_engine/wiki_operations.py)"]
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
| [wiki_operations](../modules/wiki_operations.md) | 0 | `source_root`, `wiki_root` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `Engine.bootstrap` | type_reference | [engine](../modules/engine.md) | — |
| `bootstrap` | type_reference | [wiki_operations](../modules/wiki_operations.md) | — |
