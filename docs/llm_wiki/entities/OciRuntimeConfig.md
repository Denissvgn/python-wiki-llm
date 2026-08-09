# OciRuntimeConfig

**Location:** `src/llm_wiki_cli/services/calibration/broker.py:306`
**Kind:** Class
**Bases:** —
**Module:** [broker](../modules/broker.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Strict local-no-egress section of a frozen execution manifest.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `runtime` | `str` | *required* | — |
| `executable` | `str` | *required* | — |
| `executable_sha256` | `str` | *required* | — |
| `worker` | `OciImageCommand` | *required* | — |
| `probe` | `OciImageCommand` | *required* | — |
| `user` | `str` | *required* | — |
| `resources` | `OciResourceLimits` | *required* | — |
| `timeout_seconds` | `int` | *required* | — |
| `termination_grace_seconds` | `int` | *required* | — |
| `max_packet_bytes` | `int` | *required* | — |
| `output_limits` | `OciOutputLimits` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_dict` | `() -> dict[str, Any]` | — | — |
| `from_dict` | `(payload: Mapping[str, Any]) -> 'OciRuntimeConfig'` | `@classmethod` | Parse an exact, credential-free OCI runtime object. |
| `from_execution_manifest` | `(payload: Mapping[str, Any]) -> 'OciRuntimeConfig'` | `@classmethod` | Extract the strict OCI object from a broader execution manifest. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["OciRuntimeConfig (src/llm_wiki_cli/services/calibration/broker.py)"]
    n1["_build_oci_run_command (src/llm_wiki_cli/services/calibration/broker.py)"]
    n2["_cleanup_timed_out_container (src/llm_wiki_cli/services/calibration/broker.py)"]
    n3["_execute_container_command (src/llm_wiki_cli/services/calibration/broker.py)"]
    n4["_validate_runtime_executable_identity (src/llm_wiki_cli/services/calibration/broker.py)"]
    n5["build_oci_dispatch_command (src/llm_wiki_cli/services/calibration/broker.py)"]
    n6["build_oci_probe_command (src/llm_wiki_cli/services/calibration/broker.py)"]
    n7["dispatch_oci_agent (src/llm_wiki_cli/services/calibration/broker.py)"]
    n8["execute_oci_admission_probe (src/llm_wiki_cli/services/calibration/broker.py)"]
    n9["OciDispatchReceipt.create (src/llm_wiki_cli/services/calibration/broker.py)"]
    n10["OciRuntimeConfig.from_dict (src/llm_wiki_cli/services/calibration/broker.py)"]
    n11["OciRuntimeConfig.from_execution_manifest (src/llm_wiki_cli/services/calibration/broker.py)"]
    n12["src/llm_wiki_cli/services/calibration/controller.py"]
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
    click n0 "../modules/broker.md"
    click n1 "../modules/broker.md"
    click n2 "../modules/broker.md"
    click n3 "../modules/broker.md"
    click n4 "../modules/broker.md"
    click n5 "../modules/broker.md"
    click n6 "../modules/broker.md"
    click n7 "../modules/broker.md"
    click n8 "../modules/broker.md"
    click n9 "../modules/broker.md"
    click n10 "../modules/broker.md"
    click n11 "../modules/broker.md"
    click n12 "../modules/controller.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [broker](../modules/broker.md) | 4 | `executable`, `executable_sha256`, `max_packet_bytes`, `output_limits`, `probe`, `resources`, `runtime`, `termination_grace_seconds`, `timeout_seconds`, `user`, `worker` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_build_oci_run_command` | type_reference | [broker](../modules/broker.md) |
| `_cleanup_timed_out_container` | type_reference | [broker](../modules/broker.md) |
| `_execute_container_command` | type_reference | [broker](../modules/broker.md) |
| `_validate_runtime_executable_identity` | type_reference | [broker](../modules/broker.md) |
| `build_oci_dispatch_command` | type_reference | [broker](../modules/broker.md) |
| `build_oci_probe_command` | type_reference | [broker](../modules/broker.md) |
| `dispatch_oci_agent` | type_reference | [broker](../modules/broker.md) |
| `execute_oci_admission_probe` | type_reference | [broker](../modules/broker.md) |
| `OciDispatchReceipt.create` | type_reference | [broker](../modules/broker.md) |
| `OciRuntimeConfig.from_dict` | type_reference | [broker](../modules/broker.md) |
| `OciRuntimeConfig.from_execution_manifest` | type_reference | [broker](../modules/broker.md) |
| `controller` | import | [controller](../modules/controller.md) |
