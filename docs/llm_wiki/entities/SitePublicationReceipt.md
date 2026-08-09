# SitePublicationReceipt

**Location:** `src/llm_wiki_cli/services/site_export.py:156`
**Kind:** Class
**Bases:** —
**Module:** [site_export](../modules/site_export.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Validated publication receipt loaded from an exported mirror.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `state` | `str` | *required* | — |
| `selection_id` | `str` | *required* | — |
| `export_id` | `str` | *required* | — |
| `selection` | `SitePublicationSelection` | *required* | — |
| `commitments` | `tuple[tuple[str, str], ...]` | *required* | — |
| `projection_hashes` | `tuple[str, ...]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SitePublicationReceipt (src/llm_wiki_cli/services/site_export.py)"]
    n1["_apply_receipt_to_report (src/llm_wiki_cli/services/site_export.py)"]
    n2["_check_marker_matches_receipt (src/llm_wiki_cli/services/site_export.py)"]
    n3["_check_publication_receipt (src/llm_wiki_cli/services/site_export.py)"]
    n4["_load_publication_receipt (src/llm_wiki_cli/services/site_export.py)"]
    n5["_selection_mismatch_issues (src/llm_wiki_cli/services/site_export.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/site_export.md"
    click n1 "../modules/site_export.md"
    click n2 "../modules/site_export.md"
    click n3 "../modules/site_export.md"
    click n4 "../modules/site_export.md"
    click n5 "../modules/site_export.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [site_export](../modules/site_export.md) | 0 | `commitments`, `export_id`, `projection_hashes`, `selection`, `selection_id`, `state` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_apply_receipt_to_report` | type_reference | [site_export](../modules/site_export.md) |
| `_check_marker_matches_receipt` | type_reference | [site_export](../modules/site_export.md) |
| `_check_publication_receipt` | type_reference | [site_export](../modules/site_export.md) |
| `_load_publication_receipt` | call | [site_export](../modules/site_export.md) |
| `_load_publication_receipt` | type_reference | [site_export](../modules/site_export.md) |
| `_selection_mismatch_issues` | type_reference | [site_export](../modules/site_export.md) |
