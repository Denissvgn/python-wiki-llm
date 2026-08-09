# P0CalibrationRun

**Location:** `src/llm_wiki_cli/services/calibration/controller.py:261`
**Kind:** Class
**Bases:** —
**Module:** [controller](../modules/controller.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Current protected controller snapshot.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `payload` | `dict[str, Any]` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `from_dict` | `(payload: Mapping[str, Any]) -> 'P0CalibrationRun'` | `@classmethod` | — |
| `cohort_id` | `() -> str` | `@property` | — |
| `state` | `() -> str` | `@property` | — |
| `generation` | `() -> int` | `@property` | — |
| `head_transition_hash` | `() -> str` | `@property` | — |
| `to_dict` | `() -> dict[str, Any]` | — | — |
| `to_json` | `() -> str` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["P0CalibrationRun (src/llm_wiki_cli/services/calibration/controller.py)"]
    n1["admit_calibration_run (src/llm_wiki_cli/api.py)"]
    n2["prepare_calibration_run (src/llm_wiki_cli/api.py)"]
    n3["record_calibration_agent_result (src/llm_wiki_cli/api.py)"]
    n4["_admit_external_broker (src/llm_wiki_cli/services/calibration/controller.py)"]
    n5["_admit_local_oci (src/llm_wiki_cli/services/calibration/controller.py)"]
    n6["_authenticate_external_attestation (src/llm_wiki_cli/services/calibration/controller.py)"]
    n7["_authenticate_external_receipt (src/llm_wiki_cli/services/calibration/controller.py)"]
    n8["_authority_freshness_failure (src/llm_wiki_cli/services/calibration/controller.py)"]
    n9["_block_ambiguous_recovery (src/llm_wiki_cli/services/calibration/controller.py)"]
    n10["_build_host_authorization (src/llm_wiki_cli/services/calibration/controller.py)"]
    n11["_build_label_field_contract (src/llm_wiki_cli/services/calibration/controller.py)"]
    n12["_build_optimizer_search_contract (src/llm_wiki_cli/services/calibration/controller.py)"]
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
    click n0 "../modules/controller.md"
    click n1 "../modules/api.md"
    click n2 "../modules/api.md"
    click n3 "../modules/api.md"
    click n4 "../modules/controller.md"
    click n5 "../modules/controller.md"
    click n6 "../modules/controller.md"
    click n7 "../modules/controller.md"
    click n8 "../modules/controller.md"
    click n9 "../modules/controller.md"
    click n10 "../modules/controller.md"
    click n11 "../modules/controller.md"
    click n12 "../modules/controller.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [controller](../modules/controller.md) | 7 | `payload` |

### References

| Reference | Kind | Source |
|---|---|---|
| `admit_calibration_run` | type_reference | [api](../modules/api.md) |
| `prepare_calibration_run` | type_reference | [api](../modules/api.md) |
| `record_calibration_agent_result` | type_reference | [api](../modules/api.md) |
| `_admit_external_broker` | type_reference | [controller](../modules/controller.md) |
| `_admit_local_oci` | type_reference | [controller](../modules/controller.md) |
| `_authenticate_external_attestation` | type_reference | [controller](../modules/controller.md) |
| `_authenticate_external_receipt` | type_reference | [controller](../modules/controller.md) |
| `_authority_freshness_failure` | type_reference | [controller](../modules/controller.md) |
| `_block_ambiguous_recovery` | type_reference | [controller](../modules/controller.md) |
| `_build_host_authorization` | type_reference | [controller](../modules/controller.md) |
| `_build_label_field_contract` | type_reference | [controller](../modules/controller.md) |
| `_build_optimizer_search_contract` | type_reference | [controller](../modules/controller.md) |
