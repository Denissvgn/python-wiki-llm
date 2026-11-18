# PathValidationError

**Location:** `src/llm_wiki_engine/path_policy.py:90`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [path_policy](../modules/path_policy.md)

## Description

Raised when a user-provided path escapes the project root.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PathValidationError (src/llm_wiki_engine/path_policy.py)"]
    n1["ValueError"]
    n2["require_committed_config (src/llm_wiki_cli/config.py)"]
    n3["require_config_inspection_unchanged (src/llm_wiki_cli/config.py)"]
    n4["require_safe_config_path (src/llm_wiki_cli/config.py)"]
    n5["src/llm_wiki_cli/services/context_packet_builder.py"]
    n6["src/llm_wiki_cli/services/context_service.py"]
    n7["src/llm_wiki_cli/services/extraction_service.py"]
    n8["src/llm_wiki_cli/services/lint_service.py"]
    n9["source_path_diagnostics (src/llm_wiki_cli/services/source_path_diagnostics.py)"]
    n10["_sync_run_options_from_request (src/llm_wiki_cli/services/sync_runtime.py)"]
    n11["validate_path (src/llm_wiki_engine/path_policy.py)"]
    n12["validate_source_paths (src/llm_wiki_engine/path_policy.py)"]
    n13["validate_source_root (src/llm_wiki_engine/path_policy.py)"]
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
    click n0 "../modules/path_policy.md"
    click n2 "../modules/config.md"
    click n3 "../modules/config.md"
    click n4 "../modules/config.md"
    click n5 "../modules/context_packet_builder.md"
    click n6 "../modules/context_service.md"
    click n7 "../modules/extraction_service.md"
    click n8 "../modules/lint_service.md"
    click n9 "../modules/source_path_diagnostics.md"
    click n10 "../modules/sync_runtime.md"
    click n11 "../modules/path_policy.md"
    click n12 "../modules/path_policy.md"
    click n13 "../modules/path_policy.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [path_policy](../modules/path_policy.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `require_committed_config` | call | [config](../modules/config.md) | 1 |
| `require_config_inspection_unchanged` | call | [config](../modules/config.md) | 1 |
| `require_safe_config_path` | call | [config](../modules/config.md) | 2 |
| `context_packet_builder` | import | [context_packet_builder](../modules/context_packet_builder.md) | — |
| `context_service` | import | [context_service](../modules/context_service.md) | — |
| `extraction_service` | import | [extraction_service](../modules/extraction_service.md) | — |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
| `source_path_diagnostics` | call | [source_path_diagnostics](../modules/source_path_diagnostics.md) | 1 |
| `_sync_run_options_from_request` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `validate_path` | call | [path_policy](../modules/path_policy.md) | 2 |
| `validate_source_paths` | call | [path_policy](../modules/path_policy.md) | 1 |
| `validate_source_root` | call | [path_policy](../modules/path_policy.md) | 6 |
