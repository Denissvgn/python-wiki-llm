# Actor

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:259`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_model](../modules/knowledge_model.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `Actor` in `src/llm_wiki_cli/services/knowledge_model.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `kind` | `ActorKind` | `ActorKind.UNKNOWN` | — |
| `actor_id` | `Optional[str]` | `None` | — |
| `version` | `Optional[str]` | `None` | — |
| `model` | `Optional[str]` | `None` | — |
| `organization` | `Optional[str]` | `None` | — |
| `extensions` | `Extensions` | `field(default_factory=dict)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `id` | `() -> Optional[str]` | `@property` | Return the wire-format actor identifier. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["Actor (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["_concept_for_page (src/llm_wiki_cli/services/knowledge_index.py)"]
    n2["_actor_to_payload (src/llm_wiki_cli/services/knowledge_model.py)"]
    n3["_parse_actor (src/llm_wiki_cli/services/knowledge_model.py)"]
    n4["_parse_semantic_facet (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/knowledge_model.md"
    click n1 "../modules/knowledge_index.md"
    click n2 "../modules/knowledge_model.md"
    click n3 "../modules/knowledge_model.md"
    click n4 "../modules/knowledge_model.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 1 | `actor_id`, `extensions`, `kind`, `model`, `organization`, `version` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_concept_for_page` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_actor_to_payload` | type_reference | [knowledge_model](../modules/knowledge_model.md) |
| `_parse_actor` | call | [knowledge_model](../modules/knowledge_model.md) |
| `_parse_actor` | type_reference | [knowledge_model](../modules/knowledge_model.md) |
| `_parse_semantic_facet` | call | [knowledge_model](../modules/knowledge_model.md) |
