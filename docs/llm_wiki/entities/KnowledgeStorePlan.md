# KnowledgeStorePlan

**Location:** `src/llm_wiki_cli/services/knowledge_storage.py:179`
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
| `member_names` | `Mapping[str, str]` | `dataclass_field(default_factory=dict, repr=False)` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeStorePlan (src/llm_wiki_cli/services/knowledge_storage.py)"]
    n1["_pack_logical (src/llm_wiki_cli/services/knowledge_packs.py)"]
    n2["build_packed_store (src/llm_wiki_cli/services/knowledge_packs.py)"]
    n3["build_storage (src/llm_wiki_cli/services/knowledge_packs.py)"]
    n4["build_knowledge_store (src/llm_wiki_cli/services/knowledge_storage.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/knowledge_storage.md"
    click n1 "../modules/knowledge_packs.md"
    click n2 "../modules/knowledge_packs.md"
    click n3 "../modules/knowledge_packs.md"
    click n4 "../modules/knowledge_storage.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_storage](../modules/knowledge_storage.md) | 0 | `member_names`, `objects`, `root_bytes`, `statistics` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_pack_logical` | call | [knowledge_packs](../modules/knowledge_packs.md) | 1 |
| `build_packed_store` | type_reference | [knowledge_packs](../modules/knowledge_packs.md) | — |
| `build_storage` | type_reference | [knowledge_packs](../modules/knowledge_packs.md) | — |
| `build_knowledge_store` | call | [knowledge_storage](../modules/knowledge_storage.md) | 1 |
| `build_knowledge_store` | type_reference | [knowledge_storage](../modules/knowledge_storage.md) | — |
