# _ApiContractResult

**Location:** `src/llm_wiki_cli/services/bootstrap_runtime.py:4146`
**Kind:** Class
**Bases:** —
**Module:** [bootstrap_runtime](../modules/bootstrap_runtime.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_ApiContractResult` in `src/llm_wiki_cli/services/bootstrap_runtime.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `contracts` | `dict \| None` | *required* | — |
| `present` | `bool` | *required* | — |
| `created` | `int` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_ApiContractResult (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n1["_append_bootstrap_log (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n2["_bootstrap_manifest_generation_state (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n3["_emit_bootstrap_complete (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n4["_emit_bootstrap_json_summary (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n5["_write_bootstrap_api_contract_page (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n6["_write_bootstrap_index (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/bootstrap_runtime.md"
    click n1 "../modules/bootstrap_runtime.md"
    click n2 "../modules/bootstrap_runtime.md"
    click n3 "../modules/bootstrap_runtime.md"
    click n4 "../modules/bootstrap_runtime.md"
    click n5 "../modules/bootstrap_runtime.md"
    click n6 "../modules/bootstrap_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [bootstrap_runtime](../modules/bootstrap_runtime.md) | 0 | `contracts`, `created`, `present` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_append_bootstrap_log` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_bootstrap_manifest_generation_state` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_emit_bootstrap_complete` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_emit_bootstrap_json_summary` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_write_bootstrap_api_contract_page` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_write_bootstrap_api_contract_page` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_write_bootstrap_api_contract_page` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_write_bootstrap_api_contract_page` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_write_bootstrap_index` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
