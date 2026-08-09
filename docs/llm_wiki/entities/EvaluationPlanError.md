# EvaluationPlanError

**Location:** `src/llm_wiki_cli/eval_lite/planner.py:63`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [planner](../modules/planner.md)

## Description

A task manifest, packet input, or capability declaration is invalid.

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
    n0["EvaluationPlanError (src/llm_wiki_cli/eval_lite/planner.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/eval_lite/__init__.py"]
    n3["_normalize_capabilities (src/llm_wiki_cli/eval_lite/planner.py)"]
    n4["_normalize_environment (src/llm_wiki_cli/eval_lite/planner.py)"]
    n5["_normalize_oracle (src/llm_wiki_cli/eval_lite/planner.py)"]
    n6["_reconciliation_receipt (src/llm_wiki_cli/eval_lite/planner.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/planner.md"
    click n2 "../modules/eval_lite___init__.md"
    click n3 "../modules/planner.md"
    click n4 "../modules/planner.md"
    click n5 "../modules/planner.md"
    click n6 "../modules/planner.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [planner](../modules/planner.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `__init__` | import | [eval_lite___init__](../modules/eval_lite___init__.md) |
| `_normalize_capabilities` | call | [planner](../modules/planner.md) |
| `_normalize_capabilities` | call | [planner](../modules/planner.md) |
| `_normalize_capabilities` | call | [planner](../modules/planner.md) |
| `_normalize_capabilities` | call | [planner](../modules/planner.md) |
| `_normalize_capabilities` | call | [planner](../modules/planner.md) |
| `_normalize_environment` | call | [planner](../modules/planner.md) |
| `_normalize_environment` | call | [planner](../modules/planner.md) |
| `_normalize_environment` | call | [planner](../modules/planner.md) |
| `_normalize_oracle` | call | [planner](../modules/planner.md) |
| `_normalize_oracle` | call | [planner](../modules/planner.md) |
| `_reconciliation_receipt` | call | [planner](../modules/planner.md) |
