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

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InfrastructureSyncError (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n3["_prior_infrastructure_state (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n4["_record_mapping (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n5["_source_hash (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n6["infrastructure_evidence_by_page (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n7["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n8["src/llm_wiki_cli/services/knowledge_generation.py"]
    n9["src/llm_wiki_cli/services/sync_runtime.py"]
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
    click n2 "../modules/bootstrap_runtime.md"
    click n3 "../modules/infrastructure_sync.md"
    click n4 "../modules/infrastructure_sync.md"
    click n5 "../modules/infrastructure_sync.md"
    click n6 "../modules/infrastructure_sync.md"
    click n7 "../modules/knowledge_artifacts.md"
    click n8 "../modules/knowledge_generation.md"
    click n9 "../modules/sync_runtime.md"
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
| `bootstrap_runtime` | import | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_prior_infrastructure_state` | call | [infrastructure_sync](../modules/infrastructure_sync.md) | 2 |
| `_record_mapping` | call | [infrastructure_sync](../modules/infrastructure_sync.md) | 14 |
| `_source_hash` | call | [infrastructure_sync](../modules/infrastructure_sync.md) | 1 |
| `infrastructure_evidence_by_page` | call | [infrastructure_sync](../modules/infrastructure_sync.md) | 1 |
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `sync_runtime` | import | [sync_runtime](../modules/sync_runtime.md) | — |
