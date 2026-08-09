# P0CalibrationIntegrityError

**Location:** `src/llm_wiki_cli/services/calibration/controller.py:233`
**Kind:** Class
**Bases:** `P0CalibrationError`
**Module:** [controller](../modules/controller.md)

## Description

Raised when protected evidence or ledger integrity is violated.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["P0CalibrationIntegrityError (src/llm_wiki_cli/services/calibration/controller.py)"]
    n1["P0CalibrationError (src/llm_wiki_cli/services/calibration/controller.py)"]
    n2["src/llm_wiki_cli/api.py"]
    n3["_assert_controls_match (src/llm_wiki_cli/services/calibration/controller.py)"]
    n4["_assert_not_link_or_reparse (src/llm_wiki_cli/services/calibration/controller.py)"]
    n5["_assert_open_evidence_directory (src/llm_wiki_cli/services/calibration/controller.py)"]
    n6["_assert_open_evidence_file (src/llm_wiki_cli/services/calibration/controller.py)"]
    n7["_assert_outbound_payload_safe (src/llm_wiki_cli/services/calibration/controller.py)"]
    n8["_assert_portable_leaf_name (src/llm_wiki_cli/services/calibration/controller.py)"]
    n9["_assert_regular_directory (src/llm_wiki_cli/services/calibration/controller.py)"]
    n10["_assert_stable_evidence_metadata (src/llm_wiki_cli/services/calibration/controller.py)"]
    n11["_authority_freshness_failure (src/llm_wiki_cli/services/calibration/controller.py)"]
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
| `_assert_controls_match` | call | [controller](../modules/controller.md) |
| `_assert_not_link_or_reparse` | call | [controller](../modules/controller.md) |
| `_assert_not_link_or_reparse` | call | [controller](../modules/controller.md) |
| `_assert_open_evidence_directory` | call | [controller](../modules/controller.md) |
| `_assert_open_evidence_file` | call | [controller](../modules/controller.md) |
| `_assert_outbound_payload_safe` | call | [controller](../modules/controller.md) |
| `_assert_portable_leaf_name` | call | [controller](../modules/controller.md) |
| `_assert_regular_directory` | call | [controller](../modules/controller.md) |
| `_assert_stable_evidence_metadata` | call | [controller](../modules/controller.md) |
| `_authority_freshness_failure` | call | [controller](../modules/controller.md) |
| `_authority_freshness_failure` | call | [controller](../modules/controller.md) |
