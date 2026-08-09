# P0CalibrationError

**Location:** `src/llm_wiki_cli/services/calibration/controller.py:225`
**Kind:** Class
**Bases:** `RuntimeError`
**Module:** [controller](../modules/controller.md)

## Description

Base error raised by the protected calibration lifecycle.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["P0CalibrationError (src/llm_wiki_cli/services/calibration/controller.py)"]
    n1["RuntimeError"]
    n2["_ExternalBrokerAuthenticationUnavailable (src/llm_wiki_cli/services/calibration/controller.py)"]
    n3["P0CalibrationIntegrityError (src/llm_wiki_cli/services/calibration/controller.py)"]
    n4["P0CalibrationRecoveryError (src/llm_wiki_cli/services/calibration/controller.py)"]
    n5["P0CalibrationSchemaError (src/llm_wiki_cli/services/calibration/controller.py)"]
    n6["P0CalibrationTransitionError (src/llm_wiki_cli/services/calibration/controller.py)"]
    n7["src/llm_wiki_cli/api.py"]
    n8["src/llm_wiki_cli/commands/docs_cmd.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/controller.md"
    click n2 "../modules/controller.md"
    click n3 "../modules/controller.md"
    click n4 "../modules/controller.md"
    click n5 "../modules/controller.md"
    click n6 "../modules/controller.md"
    click n7 "../modules/api.md"
    click n8 "../modules/docs_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [controller](../modules/controller.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `RuntimeError` | — |
| Subclass | `_ExternalBrokerAuthenticationUnavailable` | [controller](../modules/controller.md) |
| Subclass | `P0CalibrationIntegrityError` | [controller](../modules/controller.md) |
| Subclass | `P0CalibrationRecoveryError` | [controller](../modules/controller.md) |
| Subclass | `P0CalibrationSchemaError` | [controller](../modules/controller.md) |
| Subclass | `P0CalibrationTransitionError` | [controller](../modules/controller.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `api` | import | [api](../modules/api.md) |
| `docs_cmd` | import | [docs_cmd](../modules/docs_cmd.md) |
