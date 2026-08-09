# SectionOwnership

**Location:** `src/llm_wiki_cli/services/section_ownership.py:50`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [section_ownership](../modules/section_ownership.md)

## Description

The authority boundary of one parsed Markdown section.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `GENERATED` | `'generated'` | — |
| `SEMANTIC` | `'semantic'` | — |
| `MIXED` | `'mixed'` | — |
| `UNKNOWN` | `'unknown'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SectionOwnership (src/llm_wiki_cli/services/section_ownership.py)"]
    n1["Enum"]
    n2["str"]
    n3["_expected_persisted_ownership (src/llm_wiki_cli/services/section_ownership.py)"]
    n4["_normalise_section_record (src/llm_wiki_cli/services/section_ownership.py)"]
    n5["_scoped_hashes (src/llm_wiki_cli/services/section_ownership.py)"]
    n6["_top_level_policy (src/llm_wiki_cli/services/section_ownership.py)"]
    n7["classify_section_ownership (src/llm_wiki_cli/services/section_ownership.py)"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/section_ownership.md"
    click n3 "../modules/section_ownership.md"
    click n4 "../modules/section_ownership.md"
    click n5 "../modules/section_ownership.md"
    click n6 "../modules/section_ownership.md"
    click n7 "../modules/section_ownership.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [section_ownership](../modules/section_ownership.md) | 0 | `GENERATED`, `MIXED`, `SEMANTIC`, `UNKNOWN` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `_expected_persisted_ownership` | type_reference | [section_ownership](../modules/section_ownership.md) |
| `_normalise_section_record` | call | [section_ownership](../modules/section_ownership.md) |
| `_scoped_hashes` | type_reference | [section_ownership](../modules/section_ownership.md) |
| `_top_level_policy` | type_reference | [section_ownership](../modules/section_ownership.md) |
| `classify_section_ownership` | type_reference | [section_ownership](../modules/section_ownership.md) |
