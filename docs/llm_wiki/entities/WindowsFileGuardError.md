# WindowsFileGuardError

**Location:** `src/llm_wiki_cli/services/filesystem_guard.py:47`
**Kind:** Class
**Bases:** `OSError`
**Module:** [filesystem_guard](../modules/filesystem_guard.md)

## Description

Raised when a Windows input file cannot be opened without redirection.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WindowsFileGuardError (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n1["OSError"]
    n2["src/llm_wiki_cli/services/calibration/controller.py"]
    n3["src/llm_wiki_cli/services/documentation_policy.py"]
    n4["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n5["_assert_windows_regular_file_handle (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n6["_atomic_write_private_bytes_windows (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n7["_open_windows_file_metadata_guard (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n8["_open_windows_readonly_file_handle (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/filesystem_guard.md"
    click n2 "../modules/controller.md"
    click n3 "../modules/documentation_policy.md"
    click n4 "../modules/documentation_wiki_input.md"
    click n5 "../modules/filesystem_guard.md"
    click n6 "../modules/filesystem_guard.md"
    click n7 "../modules/filesystem_guard.md"
    click n8 "../modules/filesystem_guard.md"
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
| `controller` | import | [controller](../modules/controller.md) |
| `documentation_policy` | import | [documentation_policy](../modules/documentation_policy.md) |
| `documentation_wiki_input` | import | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_assert_windows_regular_file_handle` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_assert_windows_regular_file_handle` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_atomic_write_private_bytes_windows` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_open_windows_file_metadata_guard` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_open_windows_readonly_file_handle` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_open_windows_readonly_file_handle` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_open_windows_readonly_file_handle` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_open_windows_readonly_file_handle` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `_open_windows_readonly_file_handle` | call | [filesystem_guard](../modules/filesystem_guard.md) |
