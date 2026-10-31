# MaintenanceError

**Location:** `src/llm_wiki_cli/services/health_policy.py:109`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [health_policy](../modules/health_policy.md)

## Description

Maintenance evidence is absent, inconsistent or not bound to this candidate.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["MaintenanceError (src/llm_wiki_cli/services/health_policy.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/knowledge_maintenance.py"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/health_policy.md"
    click n2 "../modules/knowledge_maintenance.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [health_policy](../modules/health_policy.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_maintenance` | import | [knowledge_maintenance](../modules/knowledge_maintenance.md) | — |
