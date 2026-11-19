# StructureUpgradeResult

**Location:** `src/llm_wiki_cli/services/upgrade_runtime.py:92`
**Kind:** Class
**Bases:** —
**Module:** [upgrade_runtime](../modules/upgrade_runtime.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Paths created while refreshing the framework-owned wiki structure.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `directories` | `tuple[str, ...]` | *required* | — |
| `gitkeeps` | `tuple[str, ...]` | *required* | — |
| `files` | `tuple[str, ...]` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `created_count` | `() -> int` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["StructureUpgradeResult (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n1["_upgrade_dirs (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n1 --> n0
    click n0 "../modules/upgrade_runtime.md"
    click n1 "../modules/upgrade_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [upgrade_runtime](../modules/upgrade_runtime.md) | 1 | `directories`, `files`, `gitkeeps` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_upgrade_dirs` | call | [upgrade_runtime](../modules/upgrade_runtime.md) | 1 |
| `_upgrade_dirs` | type_reference | [upgrade_runtime](../modules/upgrade_runtime.md) | — |
