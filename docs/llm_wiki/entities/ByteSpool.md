# ByteSpool

**Location:** `src/llm_wiki_engine/storage_spool.py:21`
**Kind:** Class
**Bases:** `MutableMapping[str, bytes]`
**Module:** [storage_spool](../modules/storage_spool.md)

## Description

Owns one private temporary file and a bounded index of immutable byte captures. Each read verifies the stored SHA-256 commitment, while append and metadata quotas prevent unbounded staging. Consumers must finish before the owning context closes.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(*, max_bytes: int = 2147483648, max_index_bytes: int = 16777216, max_entry_bytes: int = MAX_OBJECT_BYTES)` | — | — |
| `__getitem__` | `(key: str) -> bytes` | — | — |
| `__setitem__` | `(key: str, value: bytes) -> None` | — | — |
| `__delitem__` | `(key: str) -> None` | — | — |
| `__iter__` | `() -> Iterator[str]` | — | — |
| `__len__` | `() -> int` | — | — |
| `__contains__` | `(key) -> bool` | — | — |
| `close` | `() -> None` | — | — |
| `fork` | `() -> ByteSpool` | — | Retain an independent index while the original owner keeps bytes alive. |
| `content_hashes` | `() -> dict[str, str]` | — | Return commitments captured while writing; reads still verify bytes. |
| `__enter__` | `()` | — | — |
| `__exit__` | `(*exc)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ByteSpool (src/llm_wiki_engine/storage_spool.py)"]
    n1["MutableMapping[str, bytes]"]
    n2["_staged_write_basis (src/llm_wiki_cli/services/sync_runtime.py)"]
    n3["src/llm_wiki_engine/knowledge_audit.py"]
    n4["build_packed_store (src/llm_wiki_engine/knowledge_packs.py)"]
    n5["prune_knowledge_storage (src/llm_wiki_engine/knowledge_storage_lifecycle.py)"]
    n6["restore_pruned_storage (src/llm_wiki_engine/knowledge_storage_lifecycle.py)"]
    n7["src/llm_wiki_engine/knowledge_stream_audit.py"]
    n8["_capture_spooled_wiki (src/llm_wiki_engine/maintenance_protocol.py)"]
    n9["maintenance_write_operation (src/llm_wiki_engine/maintenance_protocol.py)"]
    n10["ByteSpool.fork (src/llm_wiki_engine/storage_spool.py)"]
    n11["JsonSpool.__init__ (src/llm_wiki_engine/storage_spool.py)"]
    n12["spool_write (src/llm_wiki_engine/storage_spool.py)"]
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
    n11 --> n0
    n12 --> n0
    click n0 "../modules/storage_spool.md"
    click n2 "../modules/sync_runtime.md"
    click n3 "../modules/knowledge_audit.md"
    click n4 "../modules/knowledge_packs.md"
    click n5 "../modules/knowledge_storage_lifecycle.md"
    click n6 "../modules/knowledge_storage_lifecycle.md"
    click n7 "../modules/knowledge_stream_audit.md"
    click n8 "../modules/maintenance_protocol.md"
    click n9 "../modules/maintenance_protocol.md"
    click n10 "../modules/storage_spool.md"
    click n11 "../modules/storage_spool.md"
    click n12 "../modules/storage_spool.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [storage_spool](../modules/storage_spool.md) | 12 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `MutableMapping[str, bytes]` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_staged_write_basis` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `knowledge_audit` | import | [knowledge_audit](../modules/knowledge_audit.md) | — |
| `build_packed_store` | call | [knowledge_packs](../modules/knowledge_packs.md) | 1 |
| `prune_knowledge_storage` | call | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) | 1 |
| `restore_pruned_storage` | call | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) | 1 |
| `knowledge_stream_audit` | import | [knowledge_stream_audit](../modules/knowledge_stream_audit.md) | — |
| `_capture_spooled_wiki` | type_reference | [maintenance_protocol](../modules/maintenance_protocol.md) | — |
| `maintenance_write_operation` | call | [maintenance_protocol](../modules/maintenance_protocol.md) | 1 |
| `ByteSpool.fork` | type_reference | [storage_spool](../modules/storage_spool.md) | — |
| `JsonSpool.__init__` | type_reference | [storage_spool](../modules/storage_spool.md) | — |
| `spool_write` | type_reference | [storage_spool](../modules/storage_spool.md) | — |
