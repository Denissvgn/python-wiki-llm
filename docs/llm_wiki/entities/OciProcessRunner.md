# OciProcessRunner

**Location:** `src/llm_wiki_cli/services/calibration/broker.py:137`
**Kind:** Class
**Bases:** `Protocol`
**Module:** [broker](../modules/broker.md)

## Description

Dependency-injected bounded process runner.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__call__` | `(argv: Sequence[str], *, env: Mapping[str, str], timeout_seconds: int, termination_grace_seconds: int, stdout_limit: int, stderr_limit: int) -> 'BoundedProcessResult'` | — | Execute one fixed argument vector without a shell. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["OciProcessRunner (src/llm_wiki_cli/services/calibration/broker.py)"]
    n1["Protocol"]
    n2["_cleanup_timed_out_container (src/llm_wiki_cli/services/calibration/broker.py)"]
    n3["_execute_container_command (src/llm_wiki_cli/services/calibration/broker.py)"]
    n4["dispatch_oci_agent (src/llm_wiki_cli/services/calibration/broker.py)"]
    n5["execute_oci_admission_probe (src/llm_wiki_cli/services/calibration/broker.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/broker.md"
    click n2 "../modules/broker.md"
    click n3 "../modules/broker.md"
    click n4 "../modules/broker.md"
    click n5 "../modules/broker.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [broker](../modules/broker.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Protocol` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_cleanup_timed_out_container` | type_reference | [broker](../modules/broker.md) | — |
| `_execute_container_command` | type_reference | [broker](../modules/broker.md) | — |
| `dispatch_oci_agent` | type_reference | [broker](../modules/broker.md) | — |
| `execute_oci_admission_probe` | type_reference | [broker](../modules/broker.md) | — |
