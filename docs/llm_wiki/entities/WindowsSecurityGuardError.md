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
    n6["_windows_handle_owner_sid (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n7["_windows_sid_string (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n8["verify_windows_restrictive_dacl (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n9["windows_current_user_sid (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n10["windows_path_owner_sid (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n11["src/llm_wiki_cli/services/protected_artifacts.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    click n0 "../modules/filesystem_guard.md"
    click n2 "../modules/config.md"
    click n3 "../modules/filesystem_guard.md"
    click n4 "../modules/filesystem_guard.md"
    click n5 "../modules/filesystem_guard.md"
    click n6 "../modules/filesystem_guard.md"
    click n7 "../modules/filesystem_guard.md"
    click n8 "../modules/filesystem_guard.md"
    click n9 "../modules/filesystem_guard.md"
    click n10 "../modules/filesystem_guard.md"
    click n11 "../modules/protected_artifacts.md"
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

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `config` | import | [config](../modules/config.md) | — |
| `_current_windows_user_sid` | call | [filesystem_guard](../modules/filesystem_guard.md) | 3 |
| `_private_windows_security_attributes` | call | [filesystem_guard](../modules/filesystem_guard.md) | 1 |
| `_verify_windows_handle_restrictive_dacl` | call | [filesystem_guard](../modules/filesystem_guard.md) | 12 |
| `_windows_handle_owner_sid` | call | [filesystem_guard](../modules/filesystem_guard.md) | 2 |
| `_windows_sid_string` | call | [filesystem_guard](../modules/filesystem_guard.md) | 2 |
| `verify_windows_restrictive_dacl` | call | [filesystem_guard](../modules/filesystem_guard.md) | 2 |
| `windows_current_user_sid` | call | [filesystem_guard](../modules/filesystem_guard.md) | 1 |
| `windows_path_owner_sid` | call | [filesystem_guard](../modules/filesystem_guard.md) | 2 |
| `protected_artifacts` | import | [protected_artifacts](../modules/protected_artifacts.md) | — |
