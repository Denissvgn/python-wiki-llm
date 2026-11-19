# ReferenceCleanupOutcome

**Location:** `src/llm_wiki_cli/services/upgrade_runtime.py:114`
**Kind:** Class
**Bases:** —
**Module:** [upgrade_runtime](../modules/upgrade_runtime.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Whether source-reference cleanup completed and schema must roll back.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `complete` | `bool` | *required* | — |
| `restore_schema` | `bool` | `False` | — |
| `authority_changed` | `bool` | `False` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ReferenceCleanupOutcome (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n1["_migrate_reference_skill (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n1 --> n0
    click n0 "../modules/upgrade_runtime.md"
    click n1 "../modules/upgrade_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [upgrade_runtime](../modules/upgrade_runtime.md) | 0 | `authority_changed`, `complete`, `restore_schema` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_migrate_reference_skill` | call | [upgrade_runtime](../modules/upgrade_runtime.md) | 11 |
| `_migrate_reference_skill` | type_reference | [upgrade_runtime](../modules/upgrade_runtime.md) | — |
