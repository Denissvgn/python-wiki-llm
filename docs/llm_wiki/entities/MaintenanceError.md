# MaintenanceError

**Location:** `src/llm_wiki_cli/services/health_policy.py:94`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [health_policy](../modules/health_policy.md)

## Description

Maintenance evidence is absent, inconsistent or not bound to this candidate.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["MaintenanceError (src/llm_wiki_cli/services/health_policy.py)"]
    n1["ValueError"]
    n2["_binding (src/llm_wiki_cli/services/health_policy.py)"]
    n3["derive_policy (src/llm_wiki_cli/services/health_policy.py)"]
    n4["strict_json (src/llm_wiki_cli/services/health_policy.py)"]
    n5["verify_policy (src/llm_wiki_cli/services/health_policy.py)"]
    n6["_archive_binding (src/llm_wiki_cli/services/knowledge_maintenance.py)"]
    n7["_installed (src/llm_wiki_cli/services/knowledge_maintenance.py)"]
    n8["main (src/llm_wiki_cli/services/knowledge_maintenance.py)"]
    n9["preflight (src/llm_wiki_cli/services/knowledge_maintenance.py)"]
    n10["project_version (src/llm_wiki_cli/services/knowledge_maintenance.py)"]
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
    click n0 "../modules/health_policy.md"
    click n2 "../modules/health_policy.md"
    click n3 "../modules/health_policy.md"
    click n4 "../modules/health_policy.md"
    click n5 "../modules/health_policy.md"
    click n6 "../modules/knowledge_maintenance.md"
    click n7 "../modules/knowledge_maintenance.md"
    click n8 "../modules/knowledge_maintenance.md"
    click n9 "../modules/knowledge_maintenance.md"
    click n10 "../modules/knowledge_maintenance.md"
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
| `_binding` | call | [health_policy](../modules/health_policy.md) | 5 |
| `derive_policy` | call | [health_policy](../modules/health_policy.md) | 13 |
| `strict_json` | call | [health_policy](../modules/health_policy.md) | 2 |
| `verify_policy` | call | [health_policy](../modules/health_policy.md) | 1 |
| `_archive_binding` | call | [knowledge_maintenance](../modules/knowledge_maintenance.md) | 4 |
| `_installed` | call | [knowledge_maintenance](../modules/knowledge_maintenance.md) | 4 |
| `main` | call | [knowledge_maintenance](../modules/knowledge_maintenance.md) | 1 |
| `preflight` | call | [knowledge_maintenance](../modules/knowledge_maintenance.md) | 7 |
| `project_version` | call | [knowledge_maintenance](../modules/knowledge_maintenance.md) | 1 |
