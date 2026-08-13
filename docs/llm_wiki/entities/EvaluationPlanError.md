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
    n7["_require_exact_fields (src/llm_wiki_cli/eval_lite/planner.py)"]
    n8["_require_sequence (src/llm_wiki_cli/eval_lite/planner.py)"]
    n9["_require_text (src/llm_wiki_cli/eval_lite/planner.py)"]
    n10["_validate_json_tree (src/llm_wiki_cli/eval_lite/planner.py)"]
    n11["_validated_packet (src/llm_wiki_cli/eval_lite/planner.py)"]
    n12["normalize_task_manifest (src/llm_wiki_cli/eval_lite/planner.py)"]
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
    click n0 "../modules/planner.md"
    click n2 "../modules/eval_lite___init__.md"
    click n3 "../modules/planner.md"
    click n4 "../modules/planner.md"
    click n5 "../modules/planner.md"
    click n6 "../modules/planner.md"
    click n7 "../modules/planner.md"
    click n8 "../modules/planner.md"
    click n9 "../modules/planner.md"
    click n10 "../modules/planner.md"
    click n11 "../modules/planner.md"
    click n12 "../modules/planner.md"
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

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [eval_lite___init__](../modules/eval_lite___init__.md) | — |
| `_normalize_capabilities` | call | [planner](../modules/planner.md) | 5 |
| `_normalize_environment` | call | [planner](../modules/planner.md) | 3 |
| `_normalize_oracle` | call | [planner](../modules/planner.md) | 2 |
| `_reconciliation_receipt` | call | [planner](../modules/planner.md) | 7 |
| `_require_exact_fields` | call | [planner](../modules/planner.md) | 2 |
| `_require_sequence` | call | [planner](../modules/planner.md) | 4 |
| `_require_text` | call | [planner](../modules/planner.md) | 2 |
| `_validate_json_tree` | call | [planner](../modules/planner.md) | 7 |
| `_validated_packet` | call | [planner](../modules/planner.md) | 2 |
| `normalize_task_manifest` | call | [planner](../modules/planner.md) | 9 |
