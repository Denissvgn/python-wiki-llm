# FrozenDict

**Location:** `src/llm_wiki_cli/services/immutable.py:17`
**Kind:** Class
**Bases:** `dict`
**Module:** [immutable](../modules/immutable.md)

## Description

_Auto-generated from `FrozenDict` in `src/llm_wiki_cli/services/immutable.py`._

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__deepcopy__` | `(memo)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["FrozenDict (src/llm_wiki_cli/services/immutable.py)"]
    n1["dict"]
    n2["freeze (src/llm_wiki_cli/services/immutable.py)"]
    n3["src/llm_wiki_cli/services/knowledge_model.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/immutable.md"
    click n2 "../modules/immutable.md"
    click n3 "../modules/knowledge_model.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [immutable](../modules/immutable.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `dict` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `freeze` | call | [immutable](../modules/immutable.md) | 1 |
| `knowledge_model` | import | [knowledge_model](../modules/knowledge_model.md) | — |
