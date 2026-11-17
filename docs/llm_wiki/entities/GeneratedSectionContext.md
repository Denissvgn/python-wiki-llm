# _GeneratedSectionContext

**Location:** `src/llm_wiki_cli/services/sync_runtime.py:737`
**Kind:** Class
**Bases:** —
**Module:** [sync_runtime](../modules/sync_runtime.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_GeneratedSectionContext` in `src/llm_wiki_cli/services/sync_runtime.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `entity_relationship_summaries` | `Mapping[tuple[str, str], Mapping]` | *required* | — |
| `module_dependency_maps` | `dict[str, dict] \| None` | `None` | — |
| `dependency_analysis` | `dict \| None` | `None` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_GeneratedSectionContext (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1["_apply_diff (src/llm_wiki_cli/services/sync_runtime.py)"]
    n2["_build_apply_diff_context (src/llm_wiki_cli/services/sync_runtime.py)"]
    n3["_build_generated_section_context (src/llm_wiki_cli/services/sync_runtime.py)"]
    n4["_empty_generated_section_context (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/sync_runtime.md"
    click n1 "../modules/sync_runtime.md"
    click n2 "../modules/sync_runtime.md"
    click n3 "../modules/sync_runtime.md"
    click n4 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_runtime](../modules/sync_runtime.md) | 0 | `dependency_analysis`, `entity_relationship_summaries`, `module_dependency_maps` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_apply_diff` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_build_apply_diff_context` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_build_generated_section_context` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_build_generated_section_context` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_empty_generated_section_context` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_empty_generated_section_context` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
