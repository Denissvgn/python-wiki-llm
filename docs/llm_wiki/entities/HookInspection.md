# _HookInspection

**Location:** `src/llm_wiki_cli/commands/uninstall_cmd.py:62`
**Kind:** Class
**Bases:** —
**Module:** [uninstall_cmd](../modules/uninstall_cmd.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Immutable hook ownership evidence collected before mutation.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `name` | `str` | *required* | — |
| `path` | `Path` | *required* | — |
| `content` | `str` | *required* | — |
| `content_bytes` | `bytes` | *required* | — |
| `owned` | `bool` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_HookInspection (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n1["_preflight_hooks (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n2["_remove_hooks (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n3["_validate_hook_plan (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/uninstall_cmd.md"
    click n1 "../modules/uninstall_cmd.md"
    click n2 "../modules/uninstall_cmd.md"
    click n3 "../modules/uninstall_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [uninstall_cmd](../modules/uninstall_cmd.md) | 0 | `content`, `content_bytes`, `name`, `owned`, `path` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_preflight_hooks` | call | [uninstall_cmd](../modules/uninstall_cmd.md) |
| `_preflight_hooks` | type_reference | [uninstall_cmd](../modules/uninstall_cmd.md) |
| `_remove_hooks` | type_reference | [uninstall_cmd](../modules/uninstall_cmd.md) |
| `_validate_hook_plan` | type_reference | [uninstall_cmd](../modules/uninstall_cmd.md) |
