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
    n9["_calibration_packet (src/llm_wiki_cli/commands/docs_cmd.py)"]
    n10["_calibration_prepare (src/llm_wiki_cli/commands/docs_cmd.py)"]
    n11["_intake_from_args (src/llm_wiki_cli/commands/docs_cmd.py)"]
    n12["_optional_string (src/llm_wiki_cli/commands/docs_cmd.py)"]
    n13["_parse_audience_intent (src/llm_wiki_cli/commands/docs_cmd.py)"]
    n14["_read_bounded_text (src/llm_wiki_cli/commands/docs_cmd.py)"]
    n15["_read_calibration_json_object (src/llm_wiki_cli/commands/docs_cmd.py)"]
    n16["_read_json_object (src/llm_wiki_cli/commands/docs_cmd.py)"]
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
    n14 --> n0
    n15 --> n0
    n16 --> n0
    click n0 "../modules/documentation_run_contracts.md"
    click n2 "../modules/documentation_run_contracts.md"
    click n3 "../modules/documentation_run_contracts.md"
    click n4 "../modules/documentation_run_contracts.md"
    click n5 "../modules/docs_cmd.md"
    click n6 "../modules/docs_cmd.md"
    click n7 "../modules/docs_cmd.md"
    click n8 "../modules/docs_cmd.md"
    click n9 "../modules/docs_cmd.md"
    click n10 "../modules/docs_cmd.md"
    click n11 "../modules/docs_cmd.md"
    click n12 "../modules/docs_cmd.md"
    click n13 "../modules/docs_cmd.md"
    click n14 "../modules/docs_cmd.md"
    click n15 "../modules/docs_cmd.md"
    click n16 "../modules/docs_cmd.md"
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

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_assert_export_options` | call | [docs_cmd](../modules/docs_cmd.md) | 6 |
| `_bounded_calibration_json` | call | [docs_cmd](../modules/docs_cmd.md) | 2 |
| `_calibration` | call | [docs_cmd](../modules/docs_cmd.md) | 2 |
| `_calibration_json_payload` | call | [docs_cmd](../modules/docs_cmd.md) | 2 |
| `_calibration_packet` | call | [docs_cmd](../modules/docs_cmd.md) | 2 |
| `_calibration_prepare` | call | [docs_cmd](../modules/docs_cmd.md) | 1 |
| `_intake_from_args` | call | [docs_cmd](../modules/docs_cmd.md) | 8 |
| `_optional_string` | call | [docs_cmd](../modules/docs_cmd.md) | 1 |
| `_parse_audience_intent` | call | [docs_cmd](../modules/docs_cmd.md) | 1 |
| `_read_bounded_text` | call | [docs_cmd](../modules/docs_cmd.md) | 3 |
| `_read_calibration_json_object` | call | [docs_cmd](../modules/docs_cmd.md) | 6 |
| `_read_json_object` | call | [docs_cmd](../modules/docs_cmd.md) | 3 |

> References: showing 12 of 23 logical references; 11 omitted by the 12-row generated summary limit.
