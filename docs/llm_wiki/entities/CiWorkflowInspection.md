# _CiWorkflowInspection

**Location:** `src/llm_wiki_cli/commands/uninstall_cmd.py:121`
**Kind:** Class
**Bases:** —
**Module:** [uninstall_cmd](../modules/uninstall_cmd.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Managed CI ownership evidence collected before confirmation.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `path` | `Path` | *required* | — |
| `content` | `bytes \| None` | *required* | — |
| `removable` | `bool` | *required* | — |
| `reason` | `str \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_CiWorkflowInspection (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n1["_preflight_ci_workflow (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n2["_remove_ci_workflow (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/uninstall_cmd.md"
    click n1 "../modules/uninstall_cmd.md"
    click n2 "../modules/uninstall_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [uninstall_cmd](../modules/uninstall_cmd.md) | 0 | `content`, `path`, `reason`, `removable` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_preflight_ci_workflow` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 6 |
| `_preflight_ci_workflow` | type_reference | [uninstall_cmd](../modules/uninstall_cmd.md) | — |
| `_remove_ci_workflow` | type_reference | [uninstall_cmd](../modules/uninstall_cmd.md) | — |
