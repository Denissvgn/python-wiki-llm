# P0CalibrationAgentResult

**Location:** `src/llm_wiki_cli/services/calibration/controller.py:415`
**Kind:** Class
**Bases:** —
**Module:** [controller](../modules/controller.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Strict result returned by an intake or verifier role.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `payload` | `dict[str, Any]` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `from_dict` | `(payload: Mapping[str, Any]) -> 'P0CalibrationAgentResult'` | `@classmethod` | — |
| `result_id` | `() -> str` | `@property` | — |
| `role` | `() -> str` | `@property` | — |
| `to_dict` | `() -> dict[str, Any]` | — | — |
| `to_json` | `() -> str` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["P0CalibrationAgentResult (src/llm_wiki_cli/services/calibration/controller.py)"]
    n1["record_calibration_agent_result (src/llm_wiki_cli/api.py)"]
    n2["_record_p0_calibration_agent_result (src/llm_wiki_cli/services/calibration/controller.py)"]
    n3["_validate_result_import_bindings (src/llm_wiki_cli/services/calibration/controller.py)"]
    n4["P0CalibrationAgentResult.from_dict (src/llm_wiki_cli/services/calibration/controller.py)"]
    n5["record_calibration_agent_result (src/llm_wiki_cli/services/calibration/controller.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/controller.md"
    click n1 "../modules/api.md"
    click n2 "../modules/controller.md"
    click n3 "../modules/controller.md"
    click n4 "../modules/controller.md"
    click n5 "../modules/controller.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [controller](../modules/controller.md) | 5 | `payload` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `record_calibration_agent_result` | type_reference | [api](../modules/api.md) | — |
| `_record_p0_calibration_agent_result` | type_reference | [controller](../modules/controller.md) | — |
| `_validate_result_import_bindings` | type_reference | [controller](../modules/controller.md) | — |
| `P0CalibrationAgentResult.from_dict` | type_reference | [controller](../modules/controller.md) | — |
| `record_calibration_agent_result` | type_reference | [controller](../modules/controller.md) | — |
