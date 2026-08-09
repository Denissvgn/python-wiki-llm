# ProtectedArtifactDurabilityError

**Location:** `src/llm_wiki_cli/services/protected_artifacts.py:91`
**Kind:** Class
**Bases:** `ProtectedArtifactError`
**Module:** [protected_artifacts](../modules/protected_artifacts.md)

## Description

Raised when committed filesystem metadata cannot be made durable.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ProtectedArtifactDurabilityError (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n1["ProtectedArtifactError (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n2["_create_or_require_empty_root (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n3["_fsync_directory (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n4["ProtectedArtifactStore._open_windows_lock (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n5["ProtectedArtifactStore._write_windows (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/protected_artifacts.md"
    click n1 "../modules/protected_artifacts.md"
    click n2 "../modules/protected_artifacts.md"
    click n3 "../modules/protected_artifacts.md"
    click n4 "../modules/protected_artifacts.md"
    click n5 "../modules/protected_artifacts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [protected_artifacts](../modules/protected_artifacts.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ProtectedArtifactError` | [protected_artifacts](../modules/protected_artifacts.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `_create_or_require_empty_root` | call | [protected_artifacts](../modules/protected_artifacts.md) |
| `_fsync_directory` | call | [protected_artifacts](../modules/protected_artifacts.md) |
| `ProtectedArtifactStore._open_windows_lock` | call | [protected_artifacts](../modules/protected_artifacts.md) |
| `ProtectedArtifactStore._write_windows` | call | [protected_artifacts](../modules/protected_artifacts.md) |
