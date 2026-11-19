# SourceCleanupOutcome

**Location:** `src/llm_wiki_cli/services/upgrade_runtime.py:123`
**Kind:** Class
**Bases:** —
**Module:** [upgrade_runtime](../modules/upgrade_runtime.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Result of one recorded-source cleanup transaction.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `complete` | `bool` | *required* | — |
| `authority_changed` | `bool` | `False` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SourceCleanupOutcome (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n1["_cleanup_recorded_source (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n1 --> n0
    click n0 "../modules/upgrade_runtime.md"
    click n1 "../modules/upgrade_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [upgrade_runtime](../modules/upgrade_runtime.md) | 0 | `authority_changed`, `complete` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_cleanup_recorded_source` | call | [upgrade_runtime](../modules/upgrade_runtime.md) | 8 |
| `_cleanup_recorded_source` | type_reference | [upgrade_runtime](../modules/upgrade_runtime.md) | — |
