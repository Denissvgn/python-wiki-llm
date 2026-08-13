# BoundedProcessResult

**Location:** `src/llm_wiki_cli/services/calibration/broker.py:637`
**Kind:** Class
**Bases:** —
**Module:** [broker](../modules/broker.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Bounded in-memory output plus complete stream hashes and byte counts.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `started` | `bool` | *required* | — |
| `returncode` | `Optional[int]` | *required* | — |
| `timed_out` | `bool` | *required* | — |
| `error` | `Optional[str]` | *required* | — |
| `stdout` | `bytes` | *required* | — |
| `stderr` | `bytes` | *required* | — |
| `stdout_bytes` | `int` | *required* | — |
| `stderr_bytes` | `int` | *required* | — |
| `stdout_sha256` | `str` | *required* | — |
| `stderr_sha256` | `str` | *required* | — |
| `stdout_truncated` | `bool` | *required* | — |
| `stderr_truncated` | `bool` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `completed` | `(*, returncode: int = 0, stdout: bytes = b'', stderr: bytes = b'') -> 'BoundedProcessResult'` | `@classmethod` | Build deterministic bounded-process evidence with fully captured output. |
| `timeout` | `(*, stdout: bytes = b'', stderr: bytes = b'') -> 'BoundedProcessResult'` | `@classmethod` | Build deterministic bounded-process evidence for a timeout. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["BoundedProcessResult (src/llm_wiki_cli/services/calibration/broker.py)"]
    n1["_execute_container_command (src/llm_wiki_cli/services/calibration/broker.py)"]
    n2["_process_status (src/llm_wiki_cli/services/calibration/broker.py)"]
    n3["_validate_process_result_bounds (src/llm_wiki_cli/services/calibration/broker.py)"]
    n4["BoundedProcessResult.completed (src/llm_wiki_cli/services/calibration/broker.py)"]
    n5["BoundedProcessResult.timeout (src/llm_wiki_cli/services/calibration/broker.py)"]
    n6["OciDispatchReceipt.create (src/llm_wiki_cli/services/calibration/broker.py)"]
    n7["OciProcessRunner.__call__ (src/llm_wiki_cli/services/calibration/broker.py)"]
    n8["run_bounded_process (src/llm_wiki_cli/services/calibration/broker.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/broker.md"
    click n1 "../modules/broker.md"
    click n2 "../modules/broker.md"
    click n3 "../modules/broker.md"
    click n4 "../modules/broker.md"
    click n5 "../modules/broker.md"
    click n6 "../modules/broker.md"
    click n7 "../modules/broker.md"
    click n8 "../modules/broker.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [broker](../modules/broker.md) | 3 | `error`, `returncode`, `started`, `stderr`, `stderr_bytes`, `stderr_sha256`, `stderr_truncated`, `stdout`, `stdout_bytes`, `stdout_sha256`, `stdout_truncated`, `timed_out` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_execute_container_command` | type_reference | [broker](../modules/broker.md) | — |
| `_process_status` | type_reference | [broker](../modules/broker.md) | — |
| `_validate_process_result_bounds` | type_reference | [broker](../modules/broker.md) | — |
| `BoundedProcessResult.completed` | type_reference | [broker](../modules/broker.md) | — |
| `BoundedProcessResult.timeout` | type_reference | [broker](../modules/broker.md) | — |
| `OciDispatchReceipt.create` | type_reference | [broker](../modules/broker.md) | — |
| `OciProcessRunner.__call__` | type_reference | [broker](../modules/broker.md) | — |
| `run_bounded_process` | call | [broker](../modules/broker.md) | 2 |
| `run_bounded_process` | type_reference | [broker](../modules/broker.md) | — |
