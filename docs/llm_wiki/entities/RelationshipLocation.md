# RelationshipLocation

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:382`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_model](../modules/knowledge_model.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Half-open character offsets for a relationship observation.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `start` | `int` | *required* | — |
| `end` | `int` | *required* | — |
| `extensions` | `Extensions` | `field(default_factory=dict)` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["RelationshipLocation (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["_validate_builder_link (src/llm_wiki_cli/services/knowledge_index.py)"]
    n2["_build_observation (src/llm_wiki_cli/services/knowledge_links.py)"]
    n3["_parse_relationship_location (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/knowledge_model.md"
    click n1 "../modules/knowledge_index.md"
    click n2 "../modules/knowledge_links.md"
    click n3 "../modules/knowledge_model.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `end`, `extensions`, `start` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_validate_builder_link` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
| `_build_observation` | call | [knowledge_links](../modules/knowledge_links.md) | 1 |
| `_parse_relationship_location` | call | [knowledge_model](../modules/knowledge_model.md) | 1 |
| `_parse_relationship_location` | type_reference | [knowledge_model](../modules/knowledge_model.md) | — |
