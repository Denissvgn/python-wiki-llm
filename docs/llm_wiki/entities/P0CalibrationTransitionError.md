# P0CalibrationTransitionError

**Location:** `src/llm_wiki_cli/services/calibration/controller.py:237`
**Kind:** Class
**Bases:** `P0CalibrationError`
**Module:** [controller](../modules/controller.md)

## Description

Raised when a lifecycle transition is illegal or stale.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["P0CalibrationTransitionError (src/llm_wiki_cli/services/calibration/controller.py)"]
    n1["P0CalibrationError (src/llm_wiki_cli/services/calibration/controller.py)"]
    n2["src/llm_wiki_cli/api.py"]
    n3["_admit_local_oci (src/llm_wiki_cli/services/calibration/controller.py)"]
    n4["_commit_transition (src/llm_wiki_cli/services/calibration/controller.py)"]
    n5["_record_p0_calibration_agent_result (src/llm_wiki_cli/services/calibration/controller.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/controller.md"
    click n1 "../modules/controller.md"
    click n2 "../modules/api.md"
    click n3 "../modules/controller.md"
    click n4 "../modules/controller.md"
    click n5 "../modules/controller.md"
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

| Reference | Kind | Source |
|---|---|---|
| `api` | import | [api](../modules/api.md) |
| `_admit_local_oci` | call | [controller](../modules/controller.md) |
| `_commit_transition` | call | [controller](../modules/controller.md) |
| `_commit_transition` | call | [controller](../modules/controller.md) |
| `_commit_transition` | call | [controller](../modules/controller.md) |
| `_commit_transition` | call | [controller](../modules/controller.md) |
| `_commit_transition` | call | [controller](../modules/controller.md) |
| `_commit_transition` | call | [controller](../modules/controller.md) |
| `_record_p0_calibration_agent_result` | call | [controller](../modules/controller.md) |
| `_record_p0_calibration_agent_result` | call | [controller](../modules/controller.md) |
| `_record_p0_calibration_agent_result` | call | [controller](../modules/controller.md) |
| `_record_p0_calibration_agent_result` | call | [controller](../modules/controller.md) |
