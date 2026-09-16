# ByteSpool

**Location:** `src/llm_wiki_cli/services/storage_spool.py:21`
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
| `__init__` | `(*, max_bytes: int = 2147483648, max_index_bytes: int = 16777216)` | — | — |
| `__getitem__` | `(key: str) -> bytes` | — | — |
| `__setitem__` | `(key: str, value: bytes) -> None` | — | — |
| `__delitem__` | `(key: str) -> None` | — | — |
| `__iter__` | `() -> Iterator[str]` | — | — |
| `__len__` | `() -> int` | — | — |
| `__contains__` | `(key) -> bool` | — | — |
| `close` | `() -> None` | — | — |
| `__enter__` | `()` | — | — |
| `__exit__` | `(*exc)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ByteSpool (src/llm_wiki_cli/services/storage_spool.py)"]
    n1["MutableMapping[str, bytes]"]
    n2["src/llm_wiki_cli/services/knowledge_audit.py"]
    n3["build_packed_store (src/llm_wiki_cli/services/knowledge_packs.py)"]
    n4["src/llm_wiki_cli/services/knowledge_stream_audit.py"]
    n5["JsonSpool.__init__ (src/llm_wiki_cli/services/storage_spool.py)"]
    n6["spool_write (src/llm_wiki_cli/services/storage_spool.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/storage_spool.md"
    click n2 "../modules/knowledge_audit.md"
    click n3 "../modules/knowledge_packs.md"
    click n4 "../modules/knowledge_stream_audit.md"
    click n5 "../modules/storage_spool.md"
    click n6 "../modules/storage_spool.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [storage_spool](../modules/storage_spool.md) | 10 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `MutableMapping[str, bytes]` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_audit` | import | [knowledge_audit](../modules/knowledge_audit.md) | — |
| `build_packed_store` | call | [knowledge_packs](../modules/knowledge_packs.md) | 1 |
| `knowledge_stream_audit` | import | [knowledge_stream_audit](../modules/knowledge_stream_audit.md) | — |
| `JsonSpool.__init__` | type_reference | [storage_spool](../modules/storage_spool.md) | — |
| `spool_write` | type_reference | [storage_spool](../modules/storage_spool.md) | — |
