# PlannedArtifactWrite

**Location:** `src/llm_wiki_cli/services/knowledge_artifacts.py:98`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_artifacts](../modules/knowledge_artifacts.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One exact-byte action in a knowledge artifact commit.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `path` | `Path` | *required* | — |
| `relative_path` | `str` | *required* | — |
| `state` | `ArtifactWriteState` | *required* | — |
| `content_hash` | `str` | *required* | — |
| `content` | `bytes` | *required* | — |
| `needs_write` | `bool` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PlannedArtifactWrite (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n1["_apply_write (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n2["_planned_write (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n3["_verify_persisted (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/knowledge_artifacts.md"
    click n1 "../modules/knowledge_artifacts.md"
    click n2 "../modules/knowledge_artifacts.md"
    click n3 "../modules/knowledge_artifacts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_artifacts](../modules/knowledge_artifacts.md) | 0 | `content`, `content_hash`, `needs_write`, `path`, `relative_path`, `state` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_apply_write` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `_planned_write` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `_planned_write` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `_verify_persisted` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
