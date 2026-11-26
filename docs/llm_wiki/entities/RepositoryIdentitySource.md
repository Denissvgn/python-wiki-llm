# RepositoryIdentitySource

**Location:** `src/llm_wiki_engine/knowledge_model.py:239`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

How a repository identity was selected by an application-owned writer.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `CONFIGURED_PUBLIC` | `'configured-public'` | — |
| `NORMALIZED_VCS` | `'normalized-vcs'` | — |
| `UNKNOWN` | `'unknown'` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["RepositoryIdentitySource (src/llm_wiki_engine/knowledge_model.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/knowledge_orchestration.py"]
    n4["src/llm_wiki_cli/services/knowledge_projection.py"]
    n5["select_repository_identity (src/llm_wiki_engine/knowledge_envelope.py)"]
    n6["RepositoryRecord.identity_source (src/llm_wiki_engine/knowledge_model.py)"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/knowledge_model.md"
    click n3 "../modules/knowledge_orchestration.md"
    click n4 "../modules/knowledge_projection.md"
    click n5 "../modules/knowledge_envelope.md"
    click n6 "../modules/knowledge_model.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `CONFIGURED_PUBLIC`, `NORMALIZED_VCS`, `UNKNOWN` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_orchestration` | import | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `knowledge_projection` | import | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `select_repository_identity` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `RepositoryRecord.identity_source` | call | [knowledge_model](../modules/knowledge_model.md) | 1 |
| `RepositoryRecord.identity_source` | type_reference | [knowledge_model](../modules/knowledge_model.md) | — |
