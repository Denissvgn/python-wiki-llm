# OciDispatchContext

**Location:** `src/llm_wiki_cli/services/calibration/broker.py:728`
**Kind:** Class
**Bases:** —
**Module:** [broker](../modules/broker.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Controller-owned frozen value bindings for one agent attempt.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `cohort_id` | `str` | *required* | — |
| `generation` | `int` | *required* | — |
| `head_transition_hash` | `str` | *required* | — |
| `role` | `str` | *required* | — |
| `attempt` | `int` | *required* | — |
| `packet_id` | `str` | *required* | — |
| `packet_hash` | `str` | *required* | — |
| `authority_hash` | `str` | *required* | — |
| `attestation_hash` | `str` | *required* | — |
| `access_audit_hash` | `str` | *required* | — |
| `idempotency_key` | `str` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["OciDispatchContext (src/llm_wiki_cli/services/calibration/broker.py)"]
    n1["_dispatch_container_name (src/llm_wiki_cli/services/calibration/broker.py)"]
    n2["_load_agent_result (src/llm_wiki_cli/services/calibration/broker.py)"]
    n3["build_oci_dispatch_command (src/llm_wiki_cli/services/calibration/broker.py)"]
    n4["dispatch_oci_agent (src/llm_wiki_cli/services/calibration/broker.py)"]
    n5["OciDispatchReceipt.__post_init__ (src/llm_wiki_cli/services/calibration/broker.py)"]
    n6["OciDispatchReceipt.create (src/llm_wiki_cli/services/calibration/broker.py)"]
    n7["dispatch_calibration_agent (src/llm_wiki_cli/services/calibration/controller.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/broker.md"
    click n1 "../modules/broker.md"
    click n2 "../modules/broker.md"
    click n3 "../modules/broker.md"
    click n4 "../modules/broker.md"
    click n5 "../modules/broker.md"
    click n6 "../modules/broker.md"
    click n7 "../modules/controller.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [broker](../modules/broker.md) | 1 | `access_audit_hash`, `attempt`, `attestation_hash`, `authority_hash`, `cohort_id`, `generation`, `head_transition_hash`, `idempotency_key`, `packet_hash`, `packet_id`, `role` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_dispatch_container_name` | type_reference | [broker](../modules/broker.md) |
| `_load_agent_result` | type_reference | [broker](../modules/broker.md) |
| `build_oci_dispatch_command` | type_reference | [broker](../modules/broker.md) |
| `dispatch_oci_agent` | type_reference | [broker](../modules/broker.md) |
| `OciDispatchReceipt.__post_init__` | call | [broker](../modules/broker.md) |
| `OciDispatchReceipt.create` | type_reference | [broker](../modules/broker.md) |
| `dispatch_calibration_agent` | call | [controller](../modules/controller.md) |
