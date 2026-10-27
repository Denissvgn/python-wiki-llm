# ReviewAnalysis

**Location:** `src/llm_wiki_cli/services/review_service.py:99`
**Kind:** Class
**Bases:** —
**Module:** [review_service](../modules/review_service.md)

**Decorators:** `@dataclass`

## Description

Collects findings, normalized changes, page mappings, inventory and the
captured source snapshot. The optional review_scope describes bounded path
classification and physical/inventory observations without overriding
selection. Unknown or excluded scope cannot establish a negative impact
verdict; legacy construction can omit this additional disclosure.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `findings` | `list[ReviewFinding]` | *required* | — |
| `changes` | `dict` | *required* | — |
| `page_mapping` | `dict[str, list[str]]` | *required* | — |
| `inventory` | `dict` | *required* | — |
| `source_snapshot` | `SourceSnapshot` | *required* | — |
| `review_scope` | `dict \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ReviewAnalysis (src/llm_wiki_cli/services/review_service.py)"]
    n1["build_analysis (src/llm_wiki_cli/services/review_service.py)"]
    n1 --> n0
    click n0 "../modules/review_service.md"
    click n1 "../modules/review_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [review_service](../modules/review_service.md) | 0 | `changes`, `findings`, `inventory`, `page_mapping`, `review_scope`, `source_snapshot` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `build_analysis` | call | [review_service](../modules/review_service.md) | 2 |
| `build_analysis` | type_reference | [review_service](../modules/review_service.md) | — |
