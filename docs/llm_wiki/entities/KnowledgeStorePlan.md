# KnowledgeStorePlan

**Location:** `src/llm_wiki_cli/services/knowledge_storage.py:181`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_storage](../modules/knowledge_storage.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Holds the encoded root, exact immutable object bytes and storage statistics for one logical snapshot. Publication belongs to the artifact commit owner, so constructing a plan has no filesystem side effects.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `root_bytes` | `bytes` | *required* | — |
| `objects` | `Mapping[str, bytes]` | *required* | — |
| `statistics` | `Mapping[str, Any]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeStorePlan (src/llm_wiki_cli/services/knowledge_storage.py)"]
    n1["build_knowledge_store (src/llm_wiki_cli/services/knowledge_storage.py)"]
    n1 --> n0
    click n0 "../modules/knowledge_storage.md"
    click n1 "../modules/knowledge_storage.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_storage](../modules/knowledge_storage.md) | 0 | `objects`, `root_bytes`, `statistics` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `build_knowledge_store` | call | [knowledge_storage](../modules/knowledge_storage.md) | 1 |
| `build_knowledge_store` | type_reference | [knowledge_storage](../modules/knowledge_storage.md) | — |