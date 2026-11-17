# RelationshipKind

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:253`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

_Auto-generated from `RelationshipKind` in `src/llm_wiki_cli/services/knowledge_model.py`._

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `DERIVED_FROM` | `'derived_from'` | — |
| `LINKS_TO` | `'links_to'` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["RelationshipKind (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/knowledge_index.py"]
    n4["KindRegistry.with_graph_relationship_kind (src/llm_wiki_cli/services/knowledge_kinds.py)"]
    n5["KindRegistry.with_relationship_kind (src/llm_wiki_cli/services/knowledge_kinds.py)"]
    n6["src/llm_wiki_cli/services/verification_contracts.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/knowledge_model.md"
    click n3 "../modules/knowledge_index.md"
    click n4 "../modules/knowledge_kinds.md"
    click n5 "../modules/knowledge_kinds.md"
    click n6 "../modules/verification_contracts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `DERIVED_FROM`, `LINKS_TO` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_index` | import | [knowledge_index](../modules/knowledge_index.md) | — |
| `KindRegistry.with_graph_relationship_kind` | type_reference | [knowledge_kinds](../modules/knowledge_kinds.md) | — |
| `KindRegistry.with_relationship_kind` | type_reference | [knowledge_kinds](../modules/knowledge_kinds.md) | — |
| `verification_contracts` | import | [verification_contracts](../modules/verification_contracts.md) | — |
