# WindowsSecurityGuardError

**Location:** `src/llm_wiki_cli/services/filesystem_guard.py:56`
**Kind:** Class
**Bases:** `OSError`
**Module:** [filesystem_guard](../modules/filesystem_guard.md)

## Description

Raised when a Windows object lacks the required restrictive DACL.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WindowsSecurityGuardError (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n1["OSError"]
    n2["src/llm_wiki_cli/config.py"]
    n3["_current_windows_user_sid (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n4["_private_windows_security_attributes (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n5["_verify_windows_handle_restrictive_dacl (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/filesystem_guard.md"
    click n2 "../modules/config.md"
    click n3 "../modules/filesystem_guard.md"
    click n4 "../modules/filesystem_guard.md"
    click n5 "../modules/filesystem_guard.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [filesystem_guard](../modules/filesystem_guard.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `OSError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `config` | import | [config](../modules/config.md) |
| `_current_windows_user_sid` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_current_windows_user_sid` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_current_windows_user_sid` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_private_windows_security_attributes` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_verify_windows_handle_restrictive_dacl` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_verify_windows_handle_restrictive_dacl` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_verify_windows_handle_restrictive_dacl` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_verify_windows_handle_restrictive_dacl` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_verify_windows_handle_restrictive_dacl` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_verify_windows_handle_restrictive_dacl` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_verify_windows_handle_restrictive_dacl` | call | [filesystem_guard](../modules/filesystem_guard.md) |
