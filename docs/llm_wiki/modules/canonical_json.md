# canonical_json Module

**Path:** `src/llm_wiki_engine/canonical_json.py`

## Description

Streams the existing compact, sorted UTF-8 JSON representation in bounded chunks and computes exact scalar sizes. Small validated subtrees use the standard encoder; larger containers are traversed incrementally. Short-string size caching stores pure encoding results and does not establish filesystem freshness.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `collections.abc` | `Iterator`, `Mapping` |
| `functools` | `lru_cache` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `math` | `math` |
| `re` | `re` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_engine/canonical_json.py"]
    n0 --> n1
    click n1 "../modules/canonical_json.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (16) |

> All 16 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [CanonicalArray](../entities/CanonicalArray.md) | 59 | — | Explicit repeatable array stream for internal spill-backed operations. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `compact_text` | `(value: Any, *, allow_nan: bool = False) -> str` | — | — |
| `compact_bytes` | `(value: Any, *, allow_nan: bool = False) -> bytes` | — | — |
| `compact_line_bytes` | `(value: Any) -> bytes` | — | — |
| `ascii_compact_bytes` | `(value: Any, *, allow_nan: bool = False) -> bytes` | — | — |
| `indented_line_text` | `(value: Any) -> str` | — | — |
| `sha256_digest` | `(data: bytes) -> str` | — | The ``sha256:<hex>`` wire form of a digest over raw bytes. |
| `_string_size` | `(value: str) -> int` | — | — |
| `scalar_size` | `(value: Any) -> int` | — | Exact encoded bytes, excluding a trailing newline, without JSON buffers. |
| `_fits` | `(value: Any, budget: int) -> bool` | — | — |
| `canonical_chunks` | `(value: Any, *, chunk_bytes: int = CHUNK_BYTES) -> Iterator[bytes]` | — | Emit exactly json.dumps(sort_keys=True, ensure_ascii=False, compact)+LF. |
