# ConceptKindSpec

**Location:** `src/llm_wiki_engine/knowledge_kinds.py:68`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_kinds](../modules/knowledge_kinds.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One concept kind and the page kinds its concepts may appear on.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `name` | `str` | *required* | — |
| `page_kinds` | `tuple[PageKind, ...]` | *required* | — |
| `document_only` | `bool` | `False` | — |
| `description` | `str` | `''` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ConceptKindSpec (src/llm_wiki_engine/knowledge_kinds.py)"]
    n1["src/llm_wiki_cli/engine/__init__.py"]
    n2["_builtin_concept_specs (src/llm_wiki_engine/knowledge_kinds.py)"]
    n3["KindRegistry._check_concept (src/llm_wiki_engine/knowledge_kinds.py)"]
    n4["KindRegistry.with_concept_kind (src/llm_wiki_engine/knowledge_kinds.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/knowledge_kinds.md"
    click n1 "../modules/engine___init__.md"
    click n2 "../modules/knowledge_kinds.md"
    click n3 "../modules/knowledge_kinds.md"
    click n4 "../modules/knowledge_kinds.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_kinds](../modules/knowledge_kinds.md) | 1 | `description`, `document_only`, `name`, `page_kinds` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `_builtin_concept_specs` | call | [knowledge_kinds](../modules/knowledge_kinds.md) | 1 |
| `_builtin_concept_specs` | type_reference | [knowledge_kinds](../modules/knowledge_kinds.md) | — |
| `KindRegistry._check_concept` | type_reference | [knowledge_kinds](../modules/knowledge_kinds.md) | — |
| `KindRegistry.with_concept_kind` | type_reference | [knowledge_kinds](../modules/knowledge_kinds.md) | — |
