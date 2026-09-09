# RuntimeOutputError

**Location:** `src/llm_wiki_cli/services/runtime_output.py:13`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [runtime_output](../modules/runtime_output.md)

## Description

An explicitly requested runtime destination is unusable.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["RuntimeOutputError (src/llm_wiki_cli/services/runtime_output.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/cli.py"]
    n3["_report_destination (src/llm_wiki_cli/commands/ci_check_cmd.py)"]
    n4["run (src/llm_wiki_cli/commands/ci_check_cmd.py)"]
    n5["cache_options_from_args (src/llm_wiki_cli/services/inventory_cache.py)"]
    n6["prepare_cache_options (src/llm_wiki_cli/services/inventory_cache.py)"]
    n7["prepare_destination (src/llm_wiki_cli/services/runtime_output.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/runtime_output.md"
    click n2 "../modules/cli.md"
    click n3 "../modules/ci_check_cmd.md"
    click n4 "../modules/ci_check_cmd.md"
    click n5 "../modules/inventory_cache.md"
    click n6 "../modules/inventory_cache.md"
    click n7 "../modules/runtime_output.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [runtime_output](../modules/runtime_output.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `cli` | import | [cli](../modules/cli.md) | — |
| `_report_destination` | call | [ci_check_cmd](../modules/ci_check_cmd.md) | 2 |
| `run` | call | [ci_check_cmd](../modules/ci_check_cmd.md) | 1 |
| `cache_options_from_args` | call | [inventory_cache](../modules/inventory_cache.md) | 2 |
| `prepare_cache_options` | call | [inventory_cache](../modules/inventory_cache.md) | 1 |
| `prepare_destination` | call | [runtime_output](../modules/runtime_output.md) | 1 |
