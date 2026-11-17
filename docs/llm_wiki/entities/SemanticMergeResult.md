# SemanticMergeResult

**Location:** `src/llm_wiki_cli/services/section_ownership.py:134`
**Kind:** Class
**Bases:** —
**Module:** [section_ownership](../modules/section_ownership.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Regenerated Markdown and the number of semantic values restored.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `text` | `str` | *required* | — |
| `preserved` | `int` | `0` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SemanticMergeResult (src/llm_wiki_cli/services/section_ownership.py)"]
    n1["_retain_unmarked_overload_guidance (src/llm_wiki_cli/services/section_ownership.py)"]
    n2["merge_entity_semantics (src/llm_wiki_cli/services/section_ownership.py)"]
    n3["merge_module_semantics (src/llm_wiki_cli/services/section_ownership.py)"]
    n4["merge_semantic_markdown (src/llm_wiki_cli/services/section_ownership.py)"]
    n5["_merge_entity_page (src/llm_wiki_cli/services/sync_runtime.py)"]
    n6["_merge_entity_semantics (src/llm_wiki_cli/services/sync_runtime.py)"]
    n7["_merge_module_page (src/llm_wiki_cli/services/sync_runtime.py)"]
    n8["_merge_module_semantics (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/section_ownership.md"
    click n1 "../modules/section_ownership.md"
    click n2 "../modules/section_ownership.md"
    click n3 "../modules/section_ownership.md"
    click n4 "../modules/section_ownership.md"
    click n5 "../modules/sync_runtime.md"
    click n6 "../modules/sync_runtime.md"
    click n7 "../modules/sync_runtime.md"
    click n8 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [section_ownership](../modules/section_ownership.md) | 0 | `preserved`, `text` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_retain_unmarked_overload_guidance` | call | [section_ownership](../modules/section_ownership.md) | 1 |
| `_retain_unmarked_overload_guidance` | type_reference | [section_ownership](../modules/section_ownership.md) | — |
| `merge_entity_semantics` | type_reference | [section_ownership](../modules/section_ownership.md) | — |
| `merge_module_semantics` | type_reference | [section_ownership](../modules/section_ownership.md) | — |
| `merge_semantic_markdown` | call | [section_ownership](../modules/section_ownership.md) | 1 |
| `merge_semantic_markdown` | type_reference | [section_ownership](../modules/section_ownership.md) | — |
| `_merge_entity_page` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_merge_entity_page` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_merge_entity_semantics` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_merge_module_page` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_merge_module_page` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_merge_module_semantics` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |

> References: showing 12 of 13 logical references; 1 omitted by the 12-row generated summary limit.
