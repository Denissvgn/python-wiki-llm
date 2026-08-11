# InfrastructureSyncError

**Location:** `src/llm_wiki_cli/services/infrastructure_sync.py:33`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [infrastructure_sync](../modules/infrastructure_sync.md)

## Description

Persisted infrastructure state is unsafe or internally inconsistent.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InfrastructureSyncError (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/commands/sync_cmd.py"]
    n3["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n4["_prior_infrastructure_state (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n5["_record_mapping (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n6["_source_hash (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n7["infrastructure_evidence_by_page (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n8["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n9["src/llm_wiki_cli/services/knowledge_generation.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/infrastructure_sync.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/bootstrap_runtime.md"
    click n4 "../modules/infrastructure_sync.md"
    click n5 "../modules/infrastructure_sync.md"
    click n6 "../modules/infrastructure_sync.md"
    click n7 "../modules/infrastructure_sync.md"
    click n8 "../modules/knowledge_artifacts.md"
    click n9 "../modules/knowledge_generation.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [infrastructure_sync](../modules/infrastructure_sync.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `sync_cmd` | import | [sync_cmd](../modules/sync_cmd.md) | — |
| `bootstrap_runtime` | import | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_prior_infrastructure_state` | call | [infrastructure_sync](../modules/infrastructure_sync.md) | 2 |
| `_record_mapping` | call | [infrastructure_sync](../modules/infrastructure_sync.md) | 14 |
| `_source_hash` | call | [infrastructure_sync](../modules/infrastructure_sync.md) | 1 |
| `infrastructure_evidence_by_page` | call | [infrastructure_sync](../modules/infrastructure_sync.md) | 1 |
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |
