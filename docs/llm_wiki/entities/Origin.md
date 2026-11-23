# Origin

**Location:** `src/llm_wiki_engine/knowledge_model.py:142`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

_Auto-generated from `Origin` in `src/llm_wiki_engine/knowledge_model.py`._

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `UNKNOWN` | `'unknown'` | — |
| `EXTRACTED` | `'extracted'` | — |
| `AUTHORED` | `'authored'` | — |
| `INFERRED` | `'inferred'` | — |
| `IMPORTED` | `'imported'` | — |
| `MARKDOWN` | `'markdown'` | — |
| `GOVERNANCE` | `'governance'` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["Origin (src/llm_wiki_engine/knowledge_model.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/knowledge_projection.py"]
    n4["src/llm_wiki_engine/context_packet.py"]
    n5["src/llm_wiki_engine/knowledge_artifacts.py"]
    n6["_require_structure_state (src/llm_wiki_engine/knowledge_index.py)"]
    n7["src/llm_wiki_engine/knowledge_kinds.py"]
    n8["src/llm_wiki_engine/source_retirement.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/knowledge_model.md"
    click n3 "../modules/knowledge_projection.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/knowledge_artifacts.md"
    click n6 "../modules/knowledge_index.md"
    click n7 "../modules/knowledge_kinds.md"
    click n8 "../modules/source_retirement.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `AUTHORED`, `EXTRACTED`, `GOVERNANCE`, `IMPORTED`, `INFERRED`, `MARKDOWN`, `UNKNOWN` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_projection` | import | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `context_packet` | import | [context_packet](../modules/context_packet.md) | — |
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `_require_structure_state` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `knowledge_kinds` | import | [knowledge_kinds](../modules/knowledge_kinds.md) | — |
| `source_retirement` | import | [source_retirement](../modules/source_retirement.md) | — |
