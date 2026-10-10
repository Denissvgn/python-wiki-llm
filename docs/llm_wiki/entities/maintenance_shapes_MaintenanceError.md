# MaintenanceError

**Location:** `src/llm_wiki_cli/services/maintenance_shapes.py:17`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [maintenance_shapes](../modules/maintenance_shapes.md)

## Description

_Auto-generated from `MaintenanceError` in `src/llm_wiki_cli/services/maintenance_shapes.py`._

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(code: str, message: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["MaintenanceError (src/llm_wiki_cli/services/maintenance_shapes.py)"]
    n1["ValueError"]
    n2["_current_evidence (src/llm_wiki_cli/services/maintenance_evidence.py)"]
    n3["captured_observations_from_knowledge (src/llm_wiki_cli/services/maintenance_evidence.py)"]
    n4["captured_semantic_sections (src/llm_wiki_cli/services/maintenance_evidence.py)"]
    n5["maintenance_transfers_from_page_plan (src/llm_wiki_cli/services/maintenance_evidence.py)"]
    n6["reconcile_pending_maintenance (src/llm_wiki_cli/services/maintenance_evidence.py)"]
    n7["_fields (src/llm_wiki_cli/services/maintenance_projection.py)"]
    n8["project_maintenance_knowledge (src/llm_wiki_cli/services/maintenance_projection.py)"]
    n9["validate_maintenance_binding (src/llm_wiki_cli/services/maintenance_projection.py)"]
    n10["validate_maintenance_concept_projection (src/llm_wiki_cli/services/maintenance_projection.py)"]
    n11["validate_maintenance_projection (src/llm_wiki_cli/services/maintenance_projection.py)"]
    n12["validate_maintenance_prose (src/llm_wiki_cli/services/maintenance_projection.py)"]
    n13["require (src/llm_wiki_cli/services/maintenance_shapes.py)"]
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
    click n0 "../modules/maintenance_shapes.md"
    click n2 "../modules/maintenance_evidence.md"
    click n3 "../modules/maintenance_evidence.md"
    click n4 "../modules/maintenance_evidence.md"
    click n5 "../modules/maintenance_evidence.md"
    click n6 "../modules/maintenance_evidence.md"
    click n7 "../modules/maintenance_projection.md"
    click n8 "../modules/maintenance_projection.md"
    click n9 "../modules/maintenance_projection.md"
    click n10 "../modules/maintenance_projection.md"
    click n11 "../modules/maintenance_projection.md"
    click n12 "../modules/maintenance_projection.md"
    click n13 "../modules/maintenance_shapes.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [maintenance_shapes](../modules/maintenance_shapes.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_current_evidence` | call | [maintenance_evidence](../modules/maintenance_evidence.md) | 7 |
| `captured_observations_from_knowledge` | call | [maintenance_evidence](../modules/maintenance_evidence.md) | 2 |
| `captured_semantic_sections` | call | [maintenance_evidence](../modules/maintenance_evidence.md) | 3 |
| `maintenance_transfers_from_page_plan` | call | [maintenance_evidence](../modules/maintenance_evidence.md) | 1 |
| `reconcile_pending_maintenance` | call | [maintenance_evidence](../modules/maintenance_evidence.md) | 2 |
| `_fields` | call | [maintenance_projection](../modules/maintenance_projection.md) | 1 |
| `project_maintenance_knowledge` | call | [maintenance_projection](../modules/maintenance_projection.md) | 1 |
| `validate_maintenance_binding` | call | [maintenance_projection](../modules/maintenance_projection.md) | 1 |
| `validate_maintenance_concept_projection` | call | [maintenance_projection](../modules/maintenance_projection.md) | 6 |
| `validate_maintenance_projection` | call | [maintenance_projection](../modules/maintenance_projection.md) | 5 |
| `validate_maintenance_prose` | call | [maintenance_projection](../modules/maintenance_projection.md) | 4 |
| `require` | call | [maintenance_shapes](../modules/maintenance_shapes.md) | 1 |

> References: showing 12 of 33 logical references; 21 omitted by the 12-row generated summary limit.
