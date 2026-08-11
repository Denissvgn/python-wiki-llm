# ProtectedArtifactIntegrityError

**Location:** `src/llm_wiki_cli/services/protected_artifacts.py:79`
**Kind:** Class
**Bases:** `ProtectedArtifactError`
**Module:** [protected_artifacts](../modules/protected_artifacts.md)

## Description

Raised when artifact filesystem or canonical-byte invariants fail.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ProtectedArtifactIntegrityError (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n1["ProtectedArtifactError (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n2["src/llm_wiki_cli/services/calibration/controller.py"]
    n3["_assert_darwin_no_extended_acl_fd (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n4["_assert_darwin_no_extended_acl_path (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n5["_assert_directory_entries_portable (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n6["_assert_directory_fd_entries_portable (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n7["_assert_no_portable_collision_fd (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n8["_assert_path_entry_portable (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n9["_assert_path_target_regular (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n10["_assert_portable_entry_names (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n11["_assert_posix_owner_only (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n12["_assert_regular_directory (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n13["_assert_regular_directory_stat (src/llm_wiki_cli/services/protected_artifacts.py)"]
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
    n12 --> n0
    n13 --> n0
    click n0 "../modules/protected_artifacts.md"
    click n1 "../modules/protected_artifacts.md"
    click n2 "../modules/controller.md"
    click n3 "../modules/protected_artifacts.md"
    click n4 "../modules/protected_artifacts.md"
    click n5 "../modules/protected_artifacts.md"
    click n6 "../modules/protected_artifacts.md"
    click n7 "../modules/protected_artifacts.md"
    click n8 "../modules/protected_artifacts.md"
    click n9 "../modules/protected_artifacts.md"
    click n10 "../modules/protected_artifacts.md"
    click n11 "../modules/protected_artifacts.md"
    click n12 "../modules/protected_artifacts.md"
    click n13 "../modules/protected_artifacts.md"
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

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `controller` | import | [controller](../modules/controller.md) | — |
| `_assert_darwin_no_extended_acl_fd` | call | [protected_artifacts](../modules/protected_artifacts.md) | 1 |
| `_assert_darwin_no_extended_acl_path` | call | [protected_artifacts](../modules/protected_artifacts.md) | 4 |
| `_assert_directory_entries_portable` | call | [protected_artifacts](../modules/protected_artifacts.md) | 1 |
| `_assert_directory_fd_entries_portable` | call | [protected_artifacts](../modules/protected_artifacts.md) | 1 |
| `_assert_no_portable_collision_fd` | call | [protected_artifacts](../modules/protected_artifacts.md) | 2 |
| `_assert_path_entry_portable` | call | [protected_artifacts](../modules/protected_artifacts.md) | 2 |
| `_assert_path_target_regular` | call | [protected_artifacts](../modules/protected_artifacts.md) | 1 |
| `_assert_portable_entry_names` | call | [protected_artifacts](../modules/protected_artifacts.md) | 1 |
| `_assert_posix_owner_only` | call | [protected_artifacts](../modules/protected_artifacts.md) | 2 |
| `_assert_regular_directory` | call | [protected_artifacts](../modules/protected_artifacts.md) | 2 |
| `_assert_regular_directory_stat` | call | [protected_artifacts](../modules/protected_artifacts.md) | 1 |

> References: showing 12 of 48 logical references; 36 omitted by the 12-row generated summary limit.
