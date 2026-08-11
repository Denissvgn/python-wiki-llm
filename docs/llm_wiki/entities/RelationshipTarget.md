# RelationshipTarget

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:391`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_model](../modules/knowledge_model.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `RelationshipTarget` in `src/llm_wiki_cli/services/knowledge_model.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `target_class` | `TargetClass` | `TargetClass.UNKNOWN` | — |
| `locator` | `Optional[str]` | `None` | — |
| `canonical_path` | `Optional[str]` | `None` | — |
| `source_path` | `Optional[str]` | `None` | — |
| `external_uri` | `Optional[str]` | `None` | — |
| `raw_target` | `Optional[str]` | `None` | — |
| `normalized_target` | `Optional[str]` | `None` | — |
| `label` | `Optional[str]` | `None` | — |
| `location` | `Optional[RelationshipLocation]` | `None` | — |
| `extensions` | `Extensions` | `field(default_factory=dict)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `endpoint_kind` | `() -> str` | `@property` | — |
| `kind` | `() -> str` | `@property` | Compatibility view of the endpoint or unresolved raw observation. |
| `value` | `() -> Optional[str]` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["RelationshipTarget (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["_derived_relationship (src/llm_wiki_cli/services/knowledge_index.py)"]
    n2["_link_relationship (src/llm_wiki_cli/services/knowledge_index.py)"]
    n3["_parse_relationship_target (src/llm_wiki_cli/services/knowledge_model.py)"]
    n4["_relationship_target_to_payload (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/knowledge_model.md"
    click n1 "../modules/knowledge_index.md"
    click n2 "../modules/knowledge_index.md"
    click n3 "../modules/knowledge_model.md"
    click n4 "../modules/knowledge_model.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 3 | `canonical_path`, `extensions`, `external_uri`, `label`, `location`, `locator`, `normalized_target`, `raw_target`, `source_path`, `target_class` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_derived_relationship` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
| `_link_relationship` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
| `_parse_relationship_target` | call | [knowledge_model](../modules/knowledge_model.md) | 1 |
| `_parse_relationship_target` | type_reference | [knowledge_model](../modules/knowledge_model.md) | — |
| `_relationship_target_to_payload` | type_reference | [knowledge_model](../modules/knowledge_model.md) | — |
