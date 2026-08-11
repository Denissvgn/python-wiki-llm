# WindowsDirectoryGuardError

**Location:** `src/llm_wiki_cli/services/filesystem_guard.py:44`
**Kind:** Class
**Bases:** `OSError`
**Module:** [filesystem_guard](../modules/filesystem_guard.md)

## Description

Raised when a Windows directory chain cannot be pinned safely.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WindowsDirectoryGuardError (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n1["OSError"]
    n2["_WindowsDirectoryGuardUnavailableError (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n3["src/llm_wiki_cli/services/calibration/controller.py"]
    n4["src/llm_wiki_cli/services/documentation_policy.py"]
    n5["src/llm_wiki_cli/services/documentation_run/dependencies.py"]
    n6["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n7["_open_windows_directory_guard (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n8["create_private_windows_directory (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n9["guard_windows_directory_chain (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n10["remove_guarded_tree (src/llm_wiki_cli/services/filesystem_guard.py)"]
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
    click n2 "../modules/filesystem_guard.md"
    click n3 "../modules/controller.md"
    click n4 "../modules/documentation_policy.md"
    click n5 "../modules/documentation_run_dependencies.md"
    click n6 "../modules/documentation_wiki_input.md"
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
| Subclass | `_WindowsDirectoryGuardUnavailableError` | [filesystem_guard](../modules/filesystem_guard.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `controller` | import | [controller](../modules/controller.md) | — |
| `documentation_policy` | import | [documentation_policy](../modules/documentation_policy.md) | — |
| `dependencies` | import | [documentation_run_dependencies](../modules/documentation_run_dependencies.md) | — |
| `documentation_wiki_input` | import | [documentation_wiki_input](../modules/documentation_wiki_input.md) | — |
| `_open_windows_directory_guard` | call | [filesystem_guard](../modules/filesystem_guard.md) | 3 |
| `create_private_windows_directory` | call | [filesystem_guard](../modules/filesystem_guard.md) | 3 |
| `guard_windows_directory_chain` | call | [filesystem_guard](../modules/filesystem_guard.md) | 4 |
| `remove_guarded_tree` | call | [filesystem_guard](../modules/filesystem_guard.md) | 5 |
| `protected_artifacts` | import | [protected_artifacts](../modules/protected_artifacts.md) | — |
