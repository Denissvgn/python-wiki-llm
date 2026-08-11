# _WindowsDirectoryGuardUnavailableError

**Location:** `src/llm_wiki_cli/services/filesystem_guard.py:48`
**Kind:** Class
**Bases:** `WindowsDirectoryGuardError`
**Module:** [filesystem_guard](../modules/filesystem_guard.md)

## Description

Raised when Windows denies access required to pin a directory.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_WindowsDirectoryGuardUnavailableError (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n1["WindowsDirectoryGuardError (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n2["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n3["_open_windows_directory_guard (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/filesystem_guard.md"
    click n1 "../modules/filesystem_guard.md"
    click n2 "../modules/documentation_wiki_input.md"
    click n3 "../modules/filesystem_guard.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [filesystem_guard](../modules/filesystem_guard.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `WindowsDirectoryGuardError` | [filesystem_guard](../modules/filesystem_guard.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `documentation_wiki_input` | import | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_open_windows_directory_guard` | call | [filesystem_guard](../modules/filesystem_guard.md) |
