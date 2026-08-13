# WindowsObjectIdentity

**Location:** `src/llm_wiki_cli/services/filesystem_guard.py:69`
**Kind:** Class
**Bases:** —
**Module:** [filesystem_guard](../modules/filesystem_guard.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Immutable Windows device and file identifier exposed by a real stat call.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `device` | `int` | *required* | — |
| `file_id` | `int` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WindowsObjectIdentity (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n1["_workspace_identity (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n2["windows_object_identity (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n3["windows_object_identity_from_values (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/filesystem_guard.md"
    click n1 "../modules/documentation_wiki_input.md"
    click n2 "../modules/filesystem_guard.md"
    click n3 "../modules/filesystem_guard.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [filesystem_guard](../modules/filesystem_guard.md) | 1 | `device`, `file_id` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_workspace_identity` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) | — |
| `windows_object_identity` | type_reference | [filesystem_guard](../modules/filesystem_guard.md) | — |
| `windows_object_identity_from_values` | call | [filesystem_guard](../modules/filesystem_guard.md) | 1 |
| `windows_object_identity_from_values` | type_reference | [filesystem_guard](../modules/filesystem_guard.md) | — |
