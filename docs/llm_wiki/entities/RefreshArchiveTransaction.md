# _RefreshArchiveTransaction

**Location:** `src/llm_wiki_cli/services/documentation_run/contracts.py:925`
**Kind:** Class
**Bases:** —
**Module:** [documentation_run_contracts](../modules/documentation_run_contracts.md)

**Decorators:** `@dataclass`

## Description

Tracks an archived run until its replacement is safely committed.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `workspace_root` | `Path \| None` | `None` | — |
| `archive` | `Path \| None` | `None` | — |
| `prior_run_id` | `str \| None` | `None` | — |
| `phase` | `str \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `active` | `() -> bool` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_RefreshArchiveTransaction (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n1["prepare_documentation_run (src/llm_wiki_cli/services/documentation_run/prepare.py)"]
    n2["_recover_interrupted_refresh (src/llm_wiki_cli/services/documentation_run/refresh.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/documentation_run_contracts.md"
    click n1 "../modules/prepare.md"
    click n2 "../modules/refresh.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_run_contracts](../modules/documentation_run_contracts.md) | 1 | `archive`, `phase`, `prior_run_id`, `workspace_root` |

### References

| Reference | Kind | Source |
|---|---|---|
| `prepare_documentation_run` | call | [prepare](../modules/prepare.md) |
| `_recover_interrupted_refresh` | call | [refresh](../modules/refresh.md) |
