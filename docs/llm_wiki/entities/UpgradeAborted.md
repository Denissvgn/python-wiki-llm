# UpgradeAborted

**Location:** `src/llm_wiki_cli/services/upgrade_runtime.py:610`
**Kind:** Class
**Bases:** `SystemExit`
**Module:** [upgrade_runtime](../modules/upgrade_runtime.md)

## Description

Upgrade stopped with an exit status; ``message`` says why when no error line did.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(code: int, message: str = '') -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["UpgradeAborted (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n1["SystemExit"]
    n2["_resolve_agent (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n3["run_request (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/upgrade_runtime.md"
    click n2 "../modules/upgrade_runtime.md"
    click n3 "../modules/upgrade_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [upgrade_runtime](../modules/upgrade_runtime.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `SystemExit` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_resolve_agent` | call | [upgrade_runtime](../modules/upgrade_runtime.md) | 2 |
| `run_request` | call | [upgrade_runtime](../modules/upgrade_runtime.md) | 26 |
