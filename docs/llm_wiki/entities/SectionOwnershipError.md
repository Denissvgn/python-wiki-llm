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
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/section_ownership.md"
    click n2 "../modules/knowledge_artifacts.md"
    click n3 "../modules/knowledge_model.md"
    click n4 "../modules/section_ownership.md"
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

| Reference | Kind | Source |
|---|---|---|
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `knowledge_model` | import | [knowledge_model](../modules/knowledge_model.md) |
| `_normalise_section_record` | call | [section_ownership](../modules/section_ownership.md) |
| `_normalise_section_record` | call | [section_ownership](../modules/section_ownership.md) |
| `_normalise_section_record` | call | [section_ownership](../modules/section_ownership.md) |
| `_normalise_section_record` | call | [section_ownership](../modules/section_ownership.md) |
| `_normalise_section_record` | call | [section_ownership](../modules/section_ownership.md) |
| `_normalise_section_record` | call | [section_ownership](../modules/section_ownership.md) |
| `_normalise_section_record` | call | [section_ownership](../modules/section_ownership.md) |
| `_normalise_section_record` | call | [section_ownership](../modules/section_ownership.md) |
| `_normalise_section_record` | call | [section_ownership](../modules/section_ownership.md) |
| `_normalise_section_record` | call | [section_ownership](../modules/section_ownership.md) |
