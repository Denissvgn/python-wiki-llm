# _BootstrapRunState

**Location:** `src/llm_wiki_cli/services/bootstrap_runtime.py:4083`
**Kind:** Class
**Bases:** —
**Module:** [bootstrap_runtime](../modules/bootstrap_runtime.md)

**Decorators:** `@dataclass`

## Description

_Auto-generated from `_BootstrapRunState` in `src/llm_wiki_cli/services/bootstrap_runtime.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `options` | `_BootstrapRunOptions` | *required* | — |
| `source_snapshot` | `Any` | `None` | — |
| `created_files` | `list[str]` | `field(default_factory=list)` | — |
| `updated_files` | `list[str]` | `field(default_factory=list)` | — |
| `skipped_files` | `list[str]` | `field(default_factory=list)` | — |
| `warnings` | `list[str]` | `field(default_factory=list)` | — |
| `unsupported_sources` | `dict[str, dict[str, object]]` | `field(default_factory=dict)` | — |
| `written_structural_page_paths` | `set[str]` | `field(default_factory=set)` | — |
| `summary` | `dict[str, Any] \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_BootstrapRunState (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n1["_append_bootstrap_log (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n2["_bootstrap_manifest_generation_state (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n3["_bootstrap_plugin_roots (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n4["_bootstrap_result (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n5["_build_bootstrap_api_contracts (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n6["_build_bootstrap_dependency_analysis (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n7["_build_bootstrap_relationships (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n8["_emit_bootstrap (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n9["_emit_bootstrap_complete (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n10["_emit_bootstrap_json_summary (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n11["_emit_bootstrap_warnings (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n12["_execute_bootstrap_options (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n1 --> n0
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
    click n10 "../modules/bootstrap_runtime.md"
    click n11 "../modules/bootstrap_runtime.md"
    click n12 "../modules/bootstrap_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [bootstrap_runtime](../modules/bootstrap_runtime.md) | 0 | `created_files`, `options`, `skipped_files`, `source_snapshot`, `summary`, `unsupported_sources`, `updated_files`, `warnings`, `written_structural_page_paths` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_append_bootstrap_log` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_bootstrap_manifest_generation_state` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_bootstrap_plugin_roots` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_bootstrap_result` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_build_bootstrap_api_contracts` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_build_bootstrap_dependency_analysis` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_build_bootstrap_relationships` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_emit_bootstrap` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_emit_bootstrap_complete` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_emit_bootstrap_json_summary` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_emit_bootstrap_warnings` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_execute_bootstrap_options` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
