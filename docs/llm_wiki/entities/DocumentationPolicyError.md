# DocumentationPolicyError

**Location:** `src/llm_wiki_cli/services/documentation_policy.py:71`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [documentation_policy](../modules/documentation_policy.md)

## Description

Raised when an external documentation policy cannot be enforced.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationPolicyError (src/llm_wiki_cli/services/documentation_policy.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/api.py"]
    n3["src/llm_wiki_cli/services/calibration/controller.py"]
    n4["_assert_safe_directory (src/llm_wiki_cli/services/documentation_policy.py)"]
    n5["_assert_safe_regular_file (src/llm_wiki_cli/services/documentation_policy.py)"]
    n6["_assert_same_file_identity (src/llm_wiki_cli/services/documentation_policy.py)"]
    n7["_assert_stable_file_metadata (src/llm_wiki_cli/services/documentation_policy.py)"]
    n8["_assert_stable_windows_path_handle_metadata (src/llm_wiki_cli/services/documentation_policy.py)"]
    n9["_guard_baseline_directory (src/llm_wiki_cli/services/documentation_policy.py)"]
    n10["_hash_file (src/llm_wiki_cli/services/documentation_policy.py)"]
    n11["_hash_windows_file (src/llm_wiki_cli/services/documentation_policy.py)"]
    n12["_lstat (src/llm_wiki_cli/services/documentation_policy.py)"]
    n13["_resolve_path (src/llm_wiki_cli/services/documentation_policy.py)"]
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
    click n0 "../modules/documentation_policy.md"
    click n2 "../modules/api.md"
    click n3 "../modules/controller.md"
    click n4 "../modules/documentation_policy.md"
    click n5 "../modules/documentation_policy.md"
    click n6 "../modules/documentation_policy.md"
    click n7 "../modules/documentation_policy.md"
    click n8 "../modules/documentation_policy.md"
    click n9 "../modules/documentation_policy.md"
    click n10 "../modules/documentation_policy.md"
    click n11 "../modules/documentation_policy.md"
    click n12 "../modules/documentation_policy.md"
    click n13 "../modules/documentation_policy.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_policy](../modules/documentation_policy.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `controller` | import | [controller](../modules/controller.md) | — |
| `_assert_safe_directory` | call | [documentation_policy](../modules/documentation_policy.md) | 3 |
| `_assert_safe_regular_file` | call | [documentation_policy](../modules/documentation_policy.md) | 3 |
| `_assert_same_file_identity` | call | [documentation_policy](../modules/documentation_policy.md) | 3 |
| `_assert_stable_file_metadata` | call | [documentation_policy](../modules/documentation_policy.md) | 1 |
| `_assert_stable_windows_path_handle_metadata` | call | [documentation_policy](../modules/documentation_policy.md) | 1 |
| `_guard_baseline_directory` | call | [documentation_policy](../modules/documentation_policy.md) | 1 |
| `_hash_file` | call | [documentation_policy](../modules/documentation_policy.md) | 3 |
| `_hash_windows_file` | call | [documentation_policy](../modules/documentation_policy.md) | 3 |
| `_lstat` | call | [documentation_policy](../modules/documentation_policy.md) | 1 |
| `_resolve_path` | call | [documentation_policy](../modules/documentation_policy.md) | 1 |

> References: showing 12 of 21 logical references; 9 omitted by the 12-row generated summary limit.
