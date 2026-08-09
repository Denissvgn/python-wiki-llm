# ProtectedArtifactLimitError

**Location:** `src/llm_wiki_cli/services/protected_artifacts.py:83`
**Kind:** Class
**Bases:** `ProtectedArtifactError`
**Module:** [protected_artifacts](../modules/protected_artifacts.md)

## Description

Raised when an artifact or protected root exceeds its byte limit.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ProtectedArtifactLimitError (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n1["ProtectedArtifactError (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n2["_assert_within_limit (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n3["_read_bounded_fd (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n4["_validate_maximum_bytes (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n5["_validate_optional_root_bytes (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n6["ProtectedArtifactStore._enforce_root_quota (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n7["ProtectedArtifactStore._read_windows (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/protected_artifacts.md"
    click n1 "../modules/protected_artifacts.md"
    click n2 "../modules/protected_artifacts.md"
    click n3 "../modules/protected_artifacts.md"
    click n4 "../modules/protected_artifacts.md"
    click n5 "../modules/protected_artifacts.md"
    click n6 "../modules/protected_artifacts.md"
    click n7 "../modules/protected_artifacts.md"
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
| `_assert_within_limit` | call | [protected_artifacts](../modules/protected_artifacts.md) |
| `_read_bounded_fd` | call | [protected_artifacts](../modules/protected_artifacts.md) |
| `_read_bounded_fd` | call | [protected_artifacts](../modules/protected_artifacts.md) |
| `_validate_maximum_bytes` | call | [protected_artifacts](../modules/protected_artifacts.md) |
| `_validate_optional_root_bytes` | call | [protected_artifacts](../modules/protected_artifacts.md) |
| `ProtectedArtifactStore._enforce_root_quota` | call | [protected_artifacts](../modules/protected_artifacts.md) |
| `ProtectedArtifactStore._read_windows` | call | [protected_artifacts](../modules/protected_artifacts.md) |
| `ProtectedArtifactStore._read_windows` | call | [protected_artifacts](../modules/protected_artifacts.md) |
