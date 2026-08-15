# _InfrastructureResult

**Location:** `src/llm_wiki_cli/services/bootstrap_runtime.py:4169`
**Kind:** Class
**Bases:** —
**Module:** [bootstrap_runtime](../modules/bootstrap_runtime.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_InfrastructureResult` in `src/llm_wiki_cli/services/bootstrap_runtime.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `entries` | `list[dict]` | *required* | — |
| `created` | `int` | *required* | — |
| `docker_inventory` | `dict` | *required* | — |
| `yaml_inventory` | `dict` | *required* | — |
| `infrastructure_inventory` | `dict` | *required* | — |
| `written_sources` | `tuple[str, ...]` | `()` | — |
| `skipped_sources` | `tuple[str, ...]` | `()` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_InfrastructureResult (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n1["_append_bootstrap_log (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n2["_bootstrap_manifest_generation_state (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n3["_emit_bootstrap_complete (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n4["_emit_bootstrap_json_summary (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n5["_infrastructure_type_count (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n6["_runtime_config_count (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n7["_runtime_config_type_counts (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n8["_write_bootstrap_index (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n9["_write_bootstrap_infrastructure_pages (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/bootstrap_runtime.md"
    click n1 "../modules/bootstrap_runtime.md"
    click n2 "../modules/bootstrap_runtime.md"
    click n3 "../modules/bootstrap_runtime.md"
    click n4 "../modules/bootstrap_runtime.md"
    click n5 "../modules/bootstrap_runtime.md"
    click n6 "../modules/bootstrap_runtime.md"
    click n7 "../modules/bootstrap_runtime.md"
    click n8 "../modules/bootstrap_runtime.md"
    click n9 "../modules/bootstrap_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [bootstrap_runtime](../modules/bootstrap_runtime.md) | 0 | `created`, `docker_inventory`, `entries`, `infrastructure_inventory`, `skipped_sources`, `written_sources`, `yaml_inventory` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_append_bootstrap_log` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_bootstrap_manifest_generation_state` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_emit_bootstrap_complete` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_emit_bootstrap_json_summary` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_infrastructure_type_count` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_runtime_config_count` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_runtime_config_type_counts` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_write_bootstrap_index` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_write_bootstrap_infrastructure_pages` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) | 1 |
| `_write_bootstrap_infrastructure_pages` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
