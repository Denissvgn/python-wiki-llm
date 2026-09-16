# KnowledgeStoreReader

**Location:** `src/llm_wiki_cli/services/knowledge_storage.py:463`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_storage](../modules/knowledge_storage.md)

## Description

Traverses hash-bound catalogs and expands only the records needed by a selected read. It enforces encoded and expanded-data limits, validates routing ownership and preserves evidence multiplicity. Full materialization additionally audits the complete logical model and secondary indexes.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(root_bytes: bytes, read_object: Callable[[str, int], bytes], *, max_bytes: int = MAX_EXPANDED_BYTES, max_objects: int = MAX_READ_OBJECTS, max_expanded_bytes: int = MAX_EXPANDED_BYTES)` | — | — |
| `_check_budget` | `() -> None` | — | — |
| `_node` | `(desc: dict[str, Any], collection: str, prefix: str) -> dict[str, Any]` | — | — |
| `records` | `(collection: str, *, owner: str \| None = None, record_id: str \| None = None) -> Iterable[dict[str, Any]]` | — | — |
| `record` | `(collection: str, owner: str, record_id: str) -> dict[str, Any]` | — | — |
| `_charge_expanded` | `(amount: int) -> None` | — | — |
| `_expand` | `(value: Any, *, stack: tuple[str, ...] = (), depth: int = 0) -> Any` | — | — |
| `expand_record` | `(row: dict[str, Any]) -> Any` | — | — |
| `materialize` | `(*, audit_routes: bool = True) -> dict[str, Any]` | — | — |
| `_audit_lookup` | `(payload: dict[str, Any]) -> None` | — | — |
| `_lookup_references` | `(selector: str) -> Iterable[dict[str, str]]` | — | — |
| `_concept_owner` | `(locator: str) -> str` | — | — |
| `_record_aliases` | `(collection: str, row: dict[str, Any], value: Any) -> set[str]` | — | — |
| `select` | `(selectors: Iterable[str], *, max_records: int = 1000) -> KnowledgeSlice` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeStoreReader (src/llm_wiki_cli/services/knowledge_storage.py)"]
    n1["PackedKnowledgeStoreReader (src/llm_wiki_cli/services/knowledge_packs.py)"]
    n2["open_knowledge_store (src/llm_wiki_cli/services/knowledge_packs.py)"]
    n3["physical_objects (src/llm_wiki_cli/services/knowledge_packs.py)"]
    n4["KnowledgeStoreReader._audit_lookup (src/llm_wiki_cli/services/knowledge_storage.py)"]
    n5["src/llm_wiki_cli/services/knowledge_storage_access.py"]
    n6["prune_knowledge_storage (src/llm_wiki_cli/services/knowledge_storage_lifecycle.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/knowledge_storage.md"
    click n1 "../modules/knowledge_packs.md"
    click n2 "../modules/knowledge_packs.md"
    click n3 "../modules/knowledge_packs.md"
    click n4 "../modules/knowledge_storage.md"
    click n5 "../modules/knowledge_storage_access.md"
    click n6 "../modules/knowledge_storage_lifecycle.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_storage](../modules/knowledge_storage.md) | 14 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Subclass | `PackedKnowledgeStoreReader` | [knowledge_packs](../modules/knowledge_packs.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `open_knowledge_store` | call | [knowledge_packs](../modules/knowledge_packs.md) | 1 |
| `open_knowledge_store` | type_reference | [knowledge_packs](../modules/knowledge_packs.md) | — |
| `physical_objects` | type_reference | [knowledge_packs](../modules/knowledge_packs.md) | — |
| `KnowledgeStoreReader._audit_lookup` | call | [knowledge_storage](../modules/knowledge_storage.md) | 1 |
| `knowledge_storage_access` | import | [knowledge_storage_access](../modules/knowledge_storage_access.md) | — |
| `prune_knowledge_storage` | call | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) | 1 |
