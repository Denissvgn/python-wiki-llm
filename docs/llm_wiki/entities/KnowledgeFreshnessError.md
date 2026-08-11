# KnowledgeFreshnessError

**Location:** `src/llm_wiki_cli/services/knowledge_freshness.py:149`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_freshness](../modules/knowledge_freshness.md)

## Description

Field-specific failure at the pure live-comparison boundary.

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
    n0["KnowledgeFreshnessError (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n1["ValueError"]
    n2["_validate_live_evaluation (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n3["_validate_live_producer (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n4["_validate_source_path (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n5["evaluate_knowledge_freshness (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/knowledge_freshness.md"
    click n2 "../modules/knowledge_freshness.md"
    click n3 "../modules/knowledge_freshness.md"
    click n4 "../modules/knowledge_freshness.md"
    click n5 "../modules/knowledge_freshness.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_freshness](../modules/knowledge_freshness.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_validate_live_evaluation` | call | [knowledge_freshness](../modules/knowledge_freshness.md) | 13 |
| `_validate_live_producer` | call | [knowledge_freshness](../modules/knowledge_freshness.md) | 1 |
| `_validate_source_path` | call | [knowledge_freshness](../modules/knowledge_freshness.md) | 4 |
| `evaluate_knowledge_freshness` | call | [knowledge_freshness](../modules/knowledge_freshness.md) | 1 |
