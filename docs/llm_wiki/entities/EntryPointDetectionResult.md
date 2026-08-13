# EntryPointDetectionResult

**Location:** `src/llm_wiki_cli/services/entrypoints.py:57`
**Kind:** Class
**Bases:** —
**Module:** [entrypoints](../modules/entrypoints.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `EntryPointDetectionResult` in `src/llm_wiki_cli/services/entrypoints.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `entries` | `list[dict]` | *required* | — |
| `warnings` | `list[str]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["EntryPointDetectionResult (src/llm_wiki_cli/services/entrypoints.py)"]
    n1["_detect_plugin_entries (src/llm_wiki_cli/services/entrypoints.py)"]
    n2["detect_entry_points (src/llm_wiki_cli/services/entrypoints.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/entrypoints.md"
    click n1 "../modules/entrypoints.md"
    click n2 "../modules/entrypoints.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [entrypoints](../modules/entrypoints.md) | 0 | `entries`, `warnings` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_detect_plugin_entries` | type_reference | [entrypoints](../modules/entrypoints.md) | — |
| `detect_entry_points` | call | [entrypoints](../modules/entrypoints.md) | 1 |
| `detect_entry_points` | type_reference | [entrypoints](../modules/entrypoints.md) | — |
