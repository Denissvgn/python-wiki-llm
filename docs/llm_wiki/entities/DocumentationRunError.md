# DocumentationRunError

**Location:** `src/llm_wiki_cli/services/documentation_run/contracts.py:235`
**Kind:** Class
**Bases:** `RuntimeError`
**Module:** [documentation_run_contracts](../modules/documentation_run_contracts.md)

## Description

Base error raised by the documentation lifecycle service.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationRunError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n1["RuntimeError"]
    n2["DocumentationIntegrityError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n3["DocumentationSchemaError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n4["DocumentationTransitionError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n5["_assert_export_options (src/llm_wiki_cli/commands/docs_cmd.py)"]
    n6["_bounded_calibration_json (src/llm_wiki_cli/commands/docs_cmd.py)"]
    n7["_calibration (src/llm_wiki_cli/commands/docs_cmd.py)"]
    n8["_calibration_json_payload (src/llm_wiki_cli/commands/docs_cmd.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/documentation_run_contracts.md"
    click n2 "../modules/documentation_run_contracts.md"
    click n3 "../modules/documentation_run_contracts.md"
    click n4 "../modules/documentation_run_contracts.md"
    click n5 "../modules/docs_cmd.md"
    click n6 "../modules/docs_cmd.md"
    click n7 "../modules/docs_cmd.md"
    click n8 "../modules/docs_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_run_contracts](../modules/documentation_run_contracts.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `RuntimeError` | — |
| Subclass | `DocumentationIntegrityError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| Subclass | `DocumentationSchemaError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| Subclass | `DocumentationTransitionError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `_assert_export_options` | call | [docs_cmd](../modules/docs_cmd.md) |
| `_assert_export_options` | call | [docs_cmd](../modules/docs_cmd.md) |
| `_assert_export_options` | call | [docs_cmd](../modules/docs_cmd.md) |
| `_assert_export_options` | call | [docs_cmd](../modules/docs_cmd.md) |
| `_assert_export_options` | call | [docs_cmd](../modules/docs_cmd.md) |
| `_assert_export_options` | call | [docs_cmd](../modules/docs_cmd.md) |
| `_bounded_calibration_json` | call | [docs_cmd](../modules/docs_cmd.md) |
| `_bounded_calibration_json` | call | [docs_cmd](../modules/docs_cmd.md) |
| `_calibration` | call | [docs_cmd](../modules/docs_cmd.md) |
| `_calibration` | call | [docs_cmd](../modules/docs_cmd.md) |
| `_calibration_json_payload` | call | [docs_cmd](../modules/docs_cmd.md) |
| `_calibration_json_payload` | call | [docs_cmd](../modules/docs_cmd.md) |
