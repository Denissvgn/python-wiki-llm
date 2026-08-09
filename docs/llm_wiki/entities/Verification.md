# Verification

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:153`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

_Auto-generated from `Verification` in `src/llm_wiki_cli/services/knowledge_model.py`._

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `UNTRACKED` | `'untracked'` | — |
| `UNVERIFIED` | `'unverified'` | — |
| `MACHINE_CHECKED` | `'machine-checked'` | — |
| `HUMAN_REVIEWED` | `'human-reviewed'` | — |
| `FAILED` | `'failed'` | — |
| `EXPIRED` | `'expired'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["Verification (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/knowledge_index.py"]
    n4["src/llm_wiki_cli/services/knowledge_projection.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    click n0 "../modules/knowledge_model.md"
    click n3 "../modules/knowledge_index.md"
    click n4 "../modules/knowledge_projection.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `EXPIRED`, `FAILED`, `HUMAN_REVIEWED`, `MACHINE_CHECKED`, `UNTRACKED`, `UNVERIFIED` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `knowledge_index` | import | [knowledge_index](../modules/knowledge_index.md) |
| `knowledge_projection` | import | [knowledge_projection](../modules/knowledge_projection.md) |
