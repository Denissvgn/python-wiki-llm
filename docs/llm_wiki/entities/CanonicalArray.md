# CanonicalArray

**Location:** `src/llm_wiki_engine/canonical_json.py:59`
**Kind:** Class
**Bases:** —
**Module:** [canonical_json](../modules/canonical_json.md)

## Description

Marks a repeatable internal array stream for canonical JSON hashing. Spill-backed audit collections supply its values without building a complete list in memory. Ordering remains the responsibility of the collection supplying the stream.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(values)` | — | — |
| `__iter__` | `()` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["CanonicalArray (src/llm_wiki_engine/canonical_json.py)"]
    n1["audit_knowledge_stream (src/llm_wiki_engine/knowledge_stream_audit.py)"]
    n1 --> n0
    click n0 "../modules/canonical_json.md"
    click n1 "../modules/knowledge_stream_audit.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [canonical_json](../modules/canonical_json.md) | 2 | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `audit_knowledge_stream` | call | [knowledge_stream_audit](../modules/knowledge_stream_audit.md) | 3 |
