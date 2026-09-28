# canonical_json Module

**Path:** `src/llm_wiki_cli/services/canonical_json.py`

## Description

Streams the existing compact, sorted UTF-8 JSON representation in bounded chunks and computes exact scalar sizes. Small validated subtrees use the standard encoder; larger containers are traversed incrementally. Short-string size caching stores pure encoding results and does not establish filesystem freshness.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `collections.abc` | `Iterator`, `Mapping` |
| `functools` | `lru_cache` |
| `json` | `json` |
| `math` | `math` |
| `re` | `re` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/canonical_json.py"]
    n1["src/llm_wiki_cli/services/knowledge_storage.py"]
    n2["src/llm_wiki_cli/services/knowledge_stream_audit.py"]
    n3["src/llm_wiki_cli/services/manifest_storage.py"]
    n1 --> n0
    n2 --> n0
    n2 --> n1
    n2 --> n3
    n3 --> n0
    n3 --> n1
    click n0 "../modules/canonical_json.md"
    click n1 "../modules/knowledge_storage.md"
    click n2 "../modules/knowledge_stream_audit.md"
    click n3 "../modules/manifest_storage.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Inbound | [knowledge_stream_audit](../modules/knowledge_stream_audit.md) |
| Inbound | [manifest_storage](../modules/manifest_storage.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [CanonicalArray](../entities/CanonicalArray.md) | 21 | — | Explicit repeatable array stream for internal spill-backed operations. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_string_size` | `(value: str) -> int` | — | — |
| `scalar_size` | `(value: Any) -> int` | — | Exact encoded bytes, excluding a trailing newline, without JSON buffers. |
| `_fits` | `(value: Any, budget: int) -> bool` | — | — |
| `canonical_chunks` | `(value: Any, *, chunk_bytes: int = CHUNK_BYTES) -> Iterator[bytes]` | — | Emit exactly json.dumps(sort_keys=True, ensure_ascii=False, compact)+LF. |