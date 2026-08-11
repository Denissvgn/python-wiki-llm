# DocumentationCalibrationError

**Location:** `src/llm_wiki_cli/services/calibration/contracts.py:91`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [calibration_contracts](../modules/calibration_contracts.md)

## Description

Raised when a calibration evidence contract is malformed.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationCalibrationError (src/llm_wiki_cli/services/calibration/contracts.py)"]
    n1["ValueError"]
    n2["_candidate_shadow (src/llm_wiki_cli/services/calibration/contracts.py)"]
    n3["_json_mapping (src/llm_wiki_cli/services/calibration/contracts.py)"]
    n4["_read_json_mapping (src/llm_wiki_cli/services/calibration/contracts.py)"]
    n5["_reason_tuple (src/llm_wiki_cli/services/calibration/contracts.py)"]
    n6["_required_flow_id (src/llm_wiki_cli/services/calibration/contracts.py)"]
    n7["build_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py)"]
    n8["build_p0_calibration_shadow (src/llm_wiki_cli/services/calibration/contracts.py)"]
    n9["evaluate_calibration_preflight (src/llm_wiki_cli/services/calibration/contracts.py)"]
    n10["mechanical_calibration_verdict (src/llm_wiki_cli/services/calibration/contracts.py)"]
    n11["validate_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py)"]
    n12["src/llm_wiki_cli/services/calibration/controller.py"]
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
    click n0 "../modules/calibration_contracts.md"
    click n2 "../modules/calibration_contracts.md"
    click n3 "../modules/calibration_contracts.md"
    click n4 "../modules/calibration_contracts.md"
    click n5 "../modules/calibration_contracts.md"
    click n6 "../modules/calibration_contracts.md"
    click n7 "../modules/calibration_contracts.md"
    click n8 "../modules/calibration_contracts.md"
    click n9 "../modules/calibration_contracts.md"
    click n10 "../modules/calibration_contracts.md"
    click n11 "../modules/calibration_contracts.md"
    click n12 "../modules/controller.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [calibration_contracts](../modules/calibration_contracts.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_candidate_shadow` | call | [calibration_contracts](../modules/calibration_contracts.md) | 3 |
| `_json_mapping` | call | [calibration_contracts](../modules/calibration_contracts.md) | 2 |
| `_read_json_mapping` | call | [calibration_contracts](../modules/calibration_contracts.md) | 3 |
| `_reason_tuple` | call | [calibration_contracts](../modules/calibration_contracts.md) | 1 |
| `_required_flow_id` | call | [calibration_contracts](../modules/calibration_contracts.md) | 1 |
| `build_flow_evidence_census` | call | [calibration_contracts](../modules/calibration_contracts.md) | 4 |
| `build_p0_calibration_shadow` | call | [calibration_contracts](../modules/calibration_contracts.md) | 5 |
| `evaluate_calibration_preflight` | call | [calibration_contracts](../modules/calibration_contracts.md) | 1 |
| `mechanical_calibration_verdict` | call | [calibration_contracts](../modules/calibration_contracts.md) | 1 |
| `validate_flow_evidence_census` | call | [calibration_contracts](../modules/calibration_contracts.md) | 24 |
| `controller` | import | [controller](../modules/controller.md) | — |
