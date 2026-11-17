# MaintenanceQueueError

**Location:** `src/llm_wiki_cli/services/maintenance_queue_format.py:122`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [maintenance_queue_format](../modules/maintenance_queue_format.md)

## Description

A maintenance queue report does not satisfy its published format.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["MaintenanceQueueError (src/llm_wiki_cli/services/maintenance_queue_format.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/engine/__init__.py"]
    n3["_bounds (src/llm_wiki_cli/services/maintenance_queue_format.py)"]
    n4["_budget (src/llm_wiki_cli/services/maintenance_queue_format.py)"]
    n5["_check_counts (src/llm_wiki_cli/services/maintenance_queue_format.py)"]
    n6["_check_coverage_gaps (src/llm_wiki_cli/services/maintenance_queue_format.py)"]
    n7["_check_custody (src/llm_wiki_cli/services/maintenance_queue_format.py)"]
    n8["_check_item (src/llm_wiki_cli/services/maintenance_queue_format.py)"]
    n9["_check_item_consistency (src/llm_wiki_cli/services/maintenance_queue_format.py)"]
    n10["_check_ordinary_review (src/llm_wiki_cli/services/maintenance_queue_format.py)"]
    n11["_check_qualification (src/llm_wiki_cli/services/maintenance_queue_format.py)"]
    n12["_choice (src/llm_wiki_cli/services/maintenance_queue_format.py)"]
    n13["_count (src/llm_wiki_cli/services/maintenance_queue_format.py)"]
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
    click n0 "../modules/maintenance_queue_format.md"
    click n2 "../modules/engine___init__.md"
    click n3 "../modules/maintenance_queue_format.md"
    click n4 "../modules/maintenance_queue_format.md"
    click n5 "../modules/maintenance_queue_format.md"
    click n6 "../modules/maintenance_queue_format.md"
    click n7 "../modules/maintenance_queue_format.md"
    click n8 "../modules/maintenance_queue_format.md"
    click n9 "../modules/maintenance_queue_format.md"
    click n10 "../modules/maintenance_queue_format.md"
    click n11 "../modules/maintenance_queue_format.md"
    click n12 "../modules/maintenance_queue_format.md"
    click n13 "../modules/maintenance_queue_format.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [maintenance_queue_format](../modules/maintenance_queue_format.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `_bounds` | call | [maintenance_queue_format](../modules/maintenance_queue_format.md) | 3 |
| `_budget` | call | [maintenance_queue_format](../modules/maintenance_queue_format.md) | 1 |
| `_check_counts` | call | [maintenance_queue_format](../modules/maintenance_queue_format.md) | 5 |
| `_check_coverage_gaps` | call | [maintenance_queue_format](../modules/maintenance_queue_format.md) | 2 |
| `_check_custody` | call | [maintenance_queue_format](../modules/maintenance_queue_format.md) | 3 |
| `_check_item` | call | [maintenance_queue_format](../modules/maintenance_queue_format.md) | 2 |
| `_check_item_consistency` | call | [maintenance_queue_format](../modules/maintenance_queue_format.md) | 7 |
| `_check_ordinary_review` | call | [maintenance_queue_format](../modules/maintenance_queue_format.md) | 5 |
| `_check_qualification` | call | [maintenance_queue_format](../modules/maintenance_queue_format.md) | 2 |
| `_choice` | call | [maintenance_queue_format](../modules/maintenance_queue_format.md) | 1 |
| `_count` | call | [maintenance_queue_format](../modules/maintenance_queue_format.md) | 1 |

> References: showing 12 of 21 logical references; 9 omitted by the 12-row generated summary limit.
