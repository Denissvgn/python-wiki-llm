# P0CalibrationSchemaError

**Location:** `src/llm_wiki_cli/services/calibration/controller.py:229`
**Kind:** Class
**Bases:** `P0CalibrationError`
**Module:** [controller](../modules/controller.md)

## Description

Raised when a calibration contract is malformed.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["P0CalibrationSchemaError (src/llm_wiki_cli/services/calibration/controller.py)"]
    n1["P0CalibrationError (src/llm_wiki_cli/services/calibration/controller.py)"]
    n2["src/llm_wiki_cli/api.py"]
    n3["_admit_external_broker (src/llm_wiki_cli/services/calibration/controller.py)"]
    n4["_authenticate_external_attestation (src/llm_wiki_cli/services/calibration/controller.py)"]
    n5["_authenticate_external_receipt (src/llm_wiki_cli/services/calibration/controller.py)"]
    n6["_json_round_trip (src/llm_wiki_cli/services/calibration/controller.py)"]
    n7["_json_round_trip_list (src/llm_wiki_cli/services/calibration/controller.py)"]
    n8["_portable_id (src/llm_wiki_cli/services/calibration/controller.py)"]
    n9["_portable_relative_path (src/llm_wiki_cli/services/calibration/controller.py)"]
    n10["_proposal_claim_records (src/llm_wiki_cli/services/calibration/controller.py)"]
    n11["_read_bound_evidence_file (src/llm_wiki_cli/services/calibration/controller.py)"]
    n12["_record_p0_calibration_agent_result (src/llm_wiki_cli/services/calibration/controller.py)"]
    n13["_require_bool (src/llm_wiki_cli/services/calibration/controller.py)"]
    n0 --> n1
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
    n13 --> n0
    click n0 "../modules/controller.md"
    click n1 "../modules/controller.md"
    click n2 "../modules/api.md"
    click n3 "../modules/controller.md"
    click n4 "../modules/controller.md"
    click n5 "../modules/controller.md"
    click n6 "../modules/controller.md"
    click n7 "../modules/controller.md"
    click n8 "../modules/controller.md"
    click n9 "../modules/controller.md"
    click n10 "../modules/controller.md"
    click n11 "../modules/controller.md"
    click n12 "../modules/controller.md"
    click n13 "../modules/controller.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [controller](../modules/controller.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `P0CalibrationError` | [controller](../modules/controller.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `_admit_external_broker` | call | [controller](../modules/controller.md) | 1 |
| `_authenticate_external_attestation` | call | [controller](../modules/controller.md) | 1 |
| `_authenticate_external_receipt` | call | [controller](../modules/controller.md) | 1 |
| `_json_round_trip` | call | [controller](../modules/controller.md) | 3 |
| `_json_round_trip_list` | call | [controller](../modules/controller.md) | 1 |
| `_portable_id` | call | [controller](../modules/controller.md) | 1 |
| `_portable_relative_path` | call | [controller](../modules/controller.md) | 2 |
| `_proposal_claim_records` | call | [controller](../modules/controller.md) | 5 |
| `_read_bound_evidence_file` | call | [controller](../modules/controller.md) | 1 |
| `_record_p0_calibration_agent_result` | call | [controller](../modules/controller.md) | 1 |
| `_require_bool` | call | [controller](../modules/controller.md) | 1 |

> References: showing 12 of 43 logical references; 31 omitted by the 12-row generated summary limit.
