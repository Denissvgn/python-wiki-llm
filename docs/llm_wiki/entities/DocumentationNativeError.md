# DocumentationNativeError

**Location:** `src/llm_wiki_cli/services/documentation_native.py:93`
**Kind:** Class
**Bases:** `RuntimeError`
**Module:** [documentation_native](../modules/documentation_native.md)

## Description

Fail-closed native evaluation or refresh error.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationNativeError (src/llm_wiki_cli/services/documentation_native.py)"]
    n1["RuntimeError"]
    n2["_collect_runtime (src/llm_wiki_cli/services/documentation_native.py)"]
    n3["_evaluate_runtime_surface (src/llm_wiki_cli/services/documentation_native.py)"]
    n4["_generation_input_paths (src/llm_wiki_cli/services/documentation_native.py)"]
    n5["_markdown_hashes (src/llm_wiki_cli/services/documentation_native.py)"]
    n6["_native_artifact_hashes (src/llm_wiki_cli/services/documentation_native.py)"]
    n7["_native_source_snapshot_preflight (src/llm_wiki_cli/services/documentation_native.py)"]
    n8["_refresh_manifest_version (src/llm_wiki_cli/services/documentation_native.py)"]
    n9["_runtime_api_contracts (src/llm_wiki_cli/services/documentation_native.py)"]
    n10["_validate_refresh_artifact_basis (src/llm_wiki_cli/services/documentation_native.py)"]
    n11["_validated_directory (src/llm_wiki_cli/services/documentation_native.py)"]
    n12["evaluate_documentation_native_freshness (src/llm_wiki_cli/services/documentation_native.py)"]
    n13["refresh_documentation_native_projection (src/llm_wiki_cli/services/documentation_native.py)"]
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
    click n0 "../modules/documentation_native.md"
    click n2 "../modules/documentation_native.md"
    click n3 "../modules/documentation_native.md"
    click n4 "../modules/documentation_native.md"
    click n5 "../modules/documentation_native.md"
    click n6 "../modules/documentation_native.md"
    click n7 "../modules/documentation_native.md"
    click n8 "../modules/documentation_native.md"
    click n9 "../modules/documentation_native.md"
    click n10 "../modules/documentation_native.md"
    click n11 "../modules/documentation_native.md"
    click n12 "../modules/documentation_native.md"
    click n13 "../modules/documentation_native.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_native](../modules/documentation_native.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `RuntimeError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_collect_runtime` | call | [documentation_native](../modules/documentation_native.md) | 3 |
| `_evaluate_runtime_surface` | call | [documentation_native](../modules/documentation_native.md) | 1 |
| `_generation_input_paths` | call | [documentation_native](../modules/documentation_native.md) | 4 |
| `_markdown_hashes` | call | [documentation_native](../modules/documentation_native.md) | 1 |
| `_native_artifact_hashes` | call | [documentation_native](../modules/documentation_native.md) | 4 |
| `_native_source_snapshot_preflight` | call | [documentation_native](../modules/documentation_native.md) | 1 |
| `_refresh_manifest_version` | call | [documentation_native](../modules/documentation_native.md) | 3 |
| `_runtime_api_contracts` | call | [documentation_native](../modules/documentation_native.md) | 1 |
| `_validate_refresh_artifact_basis` | call | [documentation_native](../modules/documentation_native.md) | 6 |
| `_validated_directory` | call | [documentation_native](../modules/documentation_native.md) | 2 |
| `evaluate_documentation_native_freshness` | call | [documentation_native](../modules/documentation_native.md) | 1 |
| `refresh_documentation_native_projection` | call | [documentation_native](../modules/documentation_native.md) | 5 |

> References: showing 12 of 13 logical references; 1 omitted by the 12-row generated summary limit.
