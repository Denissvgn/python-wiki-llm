# SectionOwnershipError

**Location:** `src/llm_wiki_cli/services/section_ownership.py:59`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [section_ownership](../modules/section_ownership.md)

## Description

Field-specific failure for the persisted section ownership contract.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SectionOwnershipError (src/llm_wiki_cli/services/section_ownership.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n3["src/llm_wiki_cli/services/knowledge_model.py"]
    n4["_normalise_section_record (src/llm_wiki_cli/services/section_ownership.py)"]
    n5["_section_array (src/llm_wiki_cli/services/section_ownership.py)"]
    n6["_section_fields (src/llm_wiki_cli/services/section_ownership.py)"]
    n7["_section_hash (src/llm_wiki_cli/services/section_ownership.py)"]
    n8["_section_int (src/llm_wiki_cli/services/section_ownership.py)"]
    n9["_section_object (src/llm_wiki_cli/services/section_ownership.py)"]
    n10["_section_string (src/llm_wiki_cli/services/section_ownership.py)"]
    n11["_section_string_array (src/llm_wiki_cli/services/section_ownership.py)"]
    n12["validate_section_ownership (src/llm_wiki_cli/services/section_ownership.py)"]
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
    click n0 "../modules/section_ownership.md"
    click n2 "../modules/knowledge_artifacts.md"
    click n3 "../modules/knowledge_model.md"
    click n4 "../modules/section_ownership.md"
    click n5 "../modules/section_ownership.md"
    click n6 "../modules/section_ownership.md"
    click n7 "../modules/section_ownership.md"
    click n8 "../modules/section_ownership.md"
    click n9 "../modules/section_ownership.md"
    click n10 "../modules/section_ownership.md"
    click n11 "../modules/section_ownership.md"
    click n12 "../modules/section_ownership.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [section_ownership](../modules/section_ownership.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `knowledge_model` | import | [knowledge_model](../modules/knowledge_model.md) | — |
| `_normalise_section_record` | call | [section_ownership](../modules/section_ownership.md) | 15 |
| `_section_array` | call | [section_ownership](../modules/section_ownership.md) | 1 |
| `_section_fields` | call | [section_ownership](../modules/section_ownership.md) | 3 |
| `_section_hash` | call | [section_ownership](../modules/section_ownership.md) | 1 |
| `_section_int` | call | [section_ownership](../modules/section_ownership.md) | 1 |
| `_section_object` | call | [section_ownership](../modules/section_ownership.md) | 1 |
| `_section_string` | call | [section_ownership](../modules/section_ownership.md) | 1 |
| `_section_string_array` | call | [section_ownership](../modules/section_ownership.md) | 1 |
| `validate_section_ownership` | call | [section_ownership](../modules/section_ownership.md) | 14 |
