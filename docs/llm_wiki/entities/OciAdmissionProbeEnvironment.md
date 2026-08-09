# OciAdmissionProbeEnvironment

**Location:** `src/llm_wiki_cli/services/calibration/broker.py:1458`
**Kind:** Class
**Bases:** —
**Module:** [broker](../modules/broker.md)

## Description

Live host evidence required to execute one admission probe.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(*, sentinels: tuple[OciProbeSentinel, ...], sentinel_identities: Mapping[str, tuple[int, int, int, int]], canary: _LocalEgressCanary) -> None` | — | — |
| `post_control_network_connections` | `() -> int` | `@property` | — |
| `assert_ready` | `() -> None` | — | — |
| `validate_request` | `(request: 'OciAdmissionProbeRequest') -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["OciAdmissionProbeEnvironment (src/llm_wiki_cli/services/calibration/broker.py)"]
    n1["_validate_probe_result_bindings (src/llm_wiki_cli/services/calibration/broker.py)"]
    n2["create_oci_admission_probe_environment (src/llm_wiki_cli/services/calibration/broker.py)"]
    n3["execute_oci_admission_probe (src/llm_wiki_cli/services/calibration/broker.py)"]
    n4["OciAdmissionProbeRequest.create (src/llm_wiki_cli/services/calibration/broker.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/broker.md"
    click n1 "../modules/broker.md"
    click n2 "../modules/broker.md"
    click n3 "../modules/broker.md"
    click n4 "../modules/broker.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [broker](../modules/broker.md) | 4 | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `_validate_probe_result_bindings` | type_reference | [broker](../modules/broker.md) |
| `create_oci_admission_probe_environment` | call | [broker](../modules/broker.md) |
| `create_oci_admission_probe_environment` | type_reference | [broker](../modules/broker.md) |
| `execute_oci_admission_probe` | type_reference | [broker](../modules/broker.md) |
| `OciAdmissionProbeRequest.create` | type_reference | [broker](../modules/broker.md) |
