# ArtifactWriteState

**Location:** `src/llm_wiki_cli/services/knowledge_artifacts.py:81`
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

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ArtifactWriteState (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/commands/migrate_cmd.py"]
    n4["src/llm_wiki_cli/commands/sync_cmd.py"]
    n5["_record_bootstrap_artifact (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/knowledge_artifacts.md"
    click n3 "../modules/migrate_cmd.md"
    click n4 "../modules/sync_cmd.md"
    click n5 "../modules/bootstrap_runtime.md"
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

| Reference | Kind | Source |
|---|---|---|
| `migrate_cmd` | import | [migrate_cmd](../modules/migrate_cmd.md) |
| `sync_cmd` | import | [sync_cmd](../modules/sync_cmd.md) |
| `_record_bootstrap_artifact` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
