# SourceSelectionError

**Location:** `src/llm_wiki_engine/source_selection.py:39`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [source_selection](../modules/source_selection.md)

## Description

Field-specific failure loading or validating source selection.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SourceSelectionError (src/llm_wiki_engine/source_selection.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/api.py"]
    n3["src/llm_wiki_cli/commands/init_cmd.py"]
    n4["src/llm_wiki_cli/services/api_contracts.py"]
    n5["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n6["src/llm_wiki_cli/services/ci_installer.py"]
    n7["src/llm_wiki_cli/services/context_service.py"]
    n8["src/llm_wiki_cli/services/documentation_native.py"]
    n9["src/llm_wiki_cli/services/documentation_policy.py"]
    n10["src/llm_wiki_cli/services/documentation_query_builder.py"]
    n11["src/llm_wiki_cli/services/documentation_run/dependencies.py"]
    n12["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n13["_source_snapshot_for_inventory_request (src/llm_wiki_cli/services/extraction_service.py)"]
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
    click n0 "../modules/source_selection.md"
    click n2 "../modules/api.md"
    click n3 "../modules/init_cmd.md"
    click n4 "../modules/api_contracts.md"
    click n5 "../modules/bootstrap_runtime.md"
    click n6 "../modules/ci_installer.md"
    click n7 "../modules/context_service.md"
    click n8 "../modules/documentation_native.md"
    click n9 "../modules/documentation_policy.md"
    click n10 "../modules/documentation_query_builder.md"
    click n11 "../modules/documentation_run_dependencies.md"
    click n12 "../modules/documentation_wiki_input.md"
    click n13 "../modules/extraction_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [source_selection](../modules/source_selection.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `init_cmd` | import | [init_cmd](../modules/init_cmd.md) | — |
| `api_contracts` | import | [api_contracts](../modules/api_contracts.md) | — |
| `bootstrap_runtime` | import | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `ci_installer` | import | [ci_installer](../modules/ci_installer.md) | — |
| `context_service` | import | [context_service](../modules/context_service.md) | — |
| `documentation_native` | import | [documentation_native](../modules/documentation_native.md) | — |
| `documentation_policy` | import | [documentation_policy](../modules/documentation_policy.md) | — |
| `documentation_query_builder` | import | [documentation_query_builder](../modules/documentation_query_builder.md) | — |
| `dependencies` | import | [documentation_run_dependencies](../modules/documentation_run_dependencies.md) | — |
| `documentation_wiki_input` | import | [documentation_wiki_input](../modules/documentation_wiki_input.md) | — |
| `_source_snapshot_for_inventory_request` | call | [extraction_service](../modules/extraction_service.md) | 2 |

> References: showing 12 of 49 logical references; 37 omitted by the 12-row generated summary limit.
