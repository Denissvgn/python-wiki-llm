# DocumentationWikiInputError

**Location:** `src/llm_wiki_cli/services/documentation_wiki_input.py:211`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [documentation_wiki_input](../modules/documentation_wiki_input.md)

## Description

Raised when a wiki cannot be adopted without weakening isolation.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(message: str, *, category: str = 'invalid_wiki_input', path: str \| None = None, rejected_entries: tuple[str, ...] = (), diagnostics: tuple[str, ...] = ()) -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationWikiInputError (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/api.py"]
    n3["src/llm_wiki_cli/services/documentation_run/integrity.py"]
    n4["_adopt_validated_wiki_snapshot (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n5["_assert_input_directory (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n6["_assert_input_regular (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n7["_assert_input_root_path_binding (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n8["_assert_safe_workspace_directory (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n9["_assert_safe_workspace_file (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n10["_assert_same_input_identity (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n11["_assert_same_workspace_identity (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n12["_assert_stable_input_metadata (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n13["_assert_windows_input_identity (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
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
    click n0 "../modules/documentation_wiki_input.md"
    click n2 "../modules/api.md"
    click n3 "../modules/integrity.md"
    click n4 "../modules/documentation_wiki_input.md"
    click n5 "../modules/documentation_wiki_input.md"
    click n6 "../modules/documentation_wiki_input.md"
    click n7 "../modules/documentation_wiki_input.md"
    click n8 "../modules/documentation_wiki_input.md"
    click n9 "../modules/documentation_wiki_input.md"
    click n10 "../modules/documentation_wiki_input.md"
    click n11 "../modules/documentation_wiki_input.md"
    click n12 "../modules/documentation_wiki_input.md"
    click n13 "../modules/documentation_wiki_input.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_wiki_input](../modules/documentation_wiki_input.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `integrity` | import | [integrity](../modules/integrity.md) | — |
| `_adopt_validated_wiki_snapshot` | call | [documentation_wiki_input](../modules/documentation_wiki_input.md) | 4 |
| `_assert_input_directory` | call | [documentation_wiki_input](../modules/documentation_wiki_input.md) | 1 |
| `_assert_input_regular` | call | [documentation_wiki_input](../modules/documentation_wiki_input.md) | 1 |
| `_assert_input_root_path_binding` | call | [documentation_wiki_input](../modules/documentation_wiki_input.md) | 1 |
| `_assert_safe_workspace_directory` | call | [documentation_wiki_input](../modules/documentation_wiki_input.md) | 2 |
| `_assert_safe_workspace_file` | call | [documentation_wiki_input](../modules/documentation_wiki_input.md) | 1 |
| `_assert_same_input_identity` | call | [documentation_wiki_input](../modules/documentation_wiki_input.md) | 1 |
| `_assert_same_workspace_identity` | call | [documentation_wiki_input](../modules/documentation_wiki_input.md) | 1 |
| `_assert_stable_input_metadata` | call | [documentation_wiki_input](../modules/documentation_wiki_input.md) | 1 |
| `_assert_windows_input_identity` | call | [documentation_wiki_input](../modules/documentation_wiki_input.md) | 2 |

> References: showing 12 of 63 logical references; 51 omitted by the 12-row generated summary limit.
