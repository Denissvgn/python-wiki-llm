# ArtifactWriteState

**Location:** `src/llm_wiki_cli/services/knowledge_artifacts.py:98`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_artifacts](../modules/knowledge_artifacts.md)

## Description

User-facing state for one planned artifact replacement.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `CREATED` | `'created'` | — |
| `UPDATED` | `'updated'` | — |
| `UNCHANGED` | `'unchanged'` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ArtifactWriteState (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n1["Enum"]
    n2["str"]
    n3["_record_bootstrap_artifact (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n4["src/llm_wiki_cli/services/knowledge_reuse.py"]
    n5["src/llm_wiki_cli/services/knowledge_storage_lifecycle.py"]
    n6["src/llm_wiki_cli/services/migrate_runtime.py"]
    n7["src/llm_wiki_cli/services/sync_runtime.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/knowledge_artifacts.md"
    click n3 "../modules/bootstrap_runtime.md"
    click n4 "../modules/knowledge_reuse.md"
    click n5 "../modules/knowledge_storage_lifecycle.md"
    click n6 "../modules/migrate_runtime.md"
    click n7 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_artifacts](../modules/knowledge_artifacts.md) | 0 | `CREATED`, `UNCHANGED`, `UPDATED` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_record_bootstrap_artifact` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `knowledge_reuse` | import | [knowledge_reuse](../modules/knowledge_reuse.md) | — |
| `knowledge_storage_lifecycle` | import | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) | — |
| `migrate_runtime` | import | [migrate_runtime](../modules/migrate_runtime.md) | — |
| `sync_runtime` | import | [sync_runtime](../modules/sync_runtime.md) | — |
