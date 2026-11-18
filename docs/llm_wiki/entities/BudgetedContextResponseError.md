# BudgetedContextResponseError

**Location:** `src/llm_wiki_cli/services/context_budget_format.py:80`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [context_budget_format](../modules/context_budget_format.md)

## Description

A budgeted context response does not follow ``llm-wiki-context/v3``.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["BudgetedContextResponseError (src/llm_wiki_cli/services/context_budget_format.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/engine/__init__.py"]
    n3["_accounting (src/llm_wiki_cli/services/context_budget_format.py)"]
    n4["_exact (src/llm_wiki_cli/services/context_budget_format.py)"]
    n5["_object (src/llm_wiki_cli/services/context_budget_format.py)"]
    n6["_portable_paths (src/llm_wiki_cli/services/context_budget_format.py)"]
    n7["_sha256 (src/llm_wiki_cli/services/context_budget_format.py)"]
    n8["_text (src/llm_wiki_cli/services/context_budget_format.py)"]
    n9["_validate (src/llm_wiki_cli/services/context_budget_format.py)"]
    n10["_validate_changes (src/llm_wiki_cli/services/context_budget_format.py)"]
    n11["_validate_context (src/llm_wiki_cli/services/context_budget_format.py)"]
    n12["_validate_invalid_request (src/llm_wiki_cli/services/context_budget_format.py)"]
    n13["_validate_metadata (src/llm_wiki_cli/services/context_budget_format.py)"]
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
    click n0 "../modules/context_budget_format.md"
    click n2 "../modules/engine___init__.md"
    click n3 "../modules/context_budget_format.md"
    click n4 "../modules/context_budget_format.md"
    click n5 "../modules/context_budget_format.md"
    click n6 "../modules/context_budget_format.md"
    click n7 "../modules/context_budget_format.md"
    click n8 "../modules/context_budget_format.md"
    click n9 "../modules/context_budget_format.md"
    click n10 "../modules/context_budget_format.md"
    click n11 "../modules/context_budget_format.md"
    click n12 "../modules/context_budget_format.md"
    click n13 "../modules/context_budget_format.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_budget_format](../modules/context_budget_format.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `_accounting` | call | [context_budget_format](../modules/context_budget_format.md) | 5 |
| `_exact` | call | [context_budget_format](../modules/context_budget_format.md) | 2 |
| `_object` | call | [context_budget_format](../modules/context_budget_format.md) | 1 |
| `_portable_paths` | call | [context_budget_format](../modules/context_budget_format.md) | 3 |
| `_sha256` | call | [context_budget_format](../modules/context_budget_format.md) | 1 |
| `_text` | call | [context_budget_format](../modules/context_budget_format.md) | 1 |
| `_validate` | call | [context_budget_format](../modules/context_budget_format.md) | 2 |
| `_validate_changes` | call | [context_budget_format](../modules/context_budget_format.md) | 9 |
| `_validate_context` | call | [context_budget_format](../modules/context_budget_format.md) | 3 |
| `_validate_invalid_request` | call | [context_budget_format](../modules/context_budget_format.md) | 1 |
| `_validate_metadata` | call | [context_budget_format](../modules/context_budget_format.md) | 2 |

> References: showing 12 of 17 logical references; 5 omitted by the 12-row generated summary limit.
