# LinkObservation

**Location:** `src/llm_wiki_cli/services/knowledge_links.py:71`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_links](../modules/knowledge_links.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One lossless link occurrence and its deterministic resolution outcome.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `source_locator` | `str` | *required* | — |
| `source_canonical_path` | `str` | *required* | — |
| `raw_target` | `str` | *required* | — |
| `normalized_target` | `str` | *required* | — |
| `label` | `str` | *required* | — |
| `location` | `RelationshipLocation` | *required* | — |
| `target_class` | `TargetClass` | *required* | — |
| `resolution` | `Resolution` | *required* | — |
| `resolved_canonical_path` | `str \| None` | `None` | — |
| `external_uri` | `str \| None` | `None` | — |
| `syntax` | `LinkSyntax` | `LinkSyntax.MARKDOWN` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `source_page` | `() -> str` | `@property` | Compatibility shorthand for the source canonical path. |
| `canonical_path` | `() -> str \| None` | `@property` | Return the resolved canonical route, when one exists. |
| `resolved_canonical_route` | `() -> str \| None` | `@property` | Compatibility alias for the resolved canonical page path. |
| `start` | `() -> int` | `@property` | — |
| `end` | `() -> int` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["LinkObservation (src/llm_wiki_cli/services/knowledge_links.py)"]
    n1["_expected_observation_outcome (src/llm_wiki_cli/services/knowledge_index.py)"]
    n2["_link_relationship (src/llm_wiki_cli/services/knowledge_index.py)"]
    n3["_observation_contains_authority_userinfo (src/llm_wiki_cli/services/knowledge_index.py)"]
    n4["_validate_builder_link (src/llm_wiki_cli/services/knowledge_index.py)"]
    n5["_validate_observation_endpoint (src/llm_wiki_cli/services/knowledge_index.py)"]
    n6["_validate_observation_source_syntax (src/llm_wiki_cli/services/knowledge_index.py)"]
    n7["_validated_observations (src/llm_wiki_cli/services/knowledge_index.py)"]
    n8["_build_observation (src/llm_wiki_cli/services/knowledge_links.py)"]
    n9["collect_link_observations (src/llm_wiki_cli/services/knowledge_links.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/knowledge_links.md"
    click n1 "../modules/knowledge_index.md"
    click n2 "../modules/knowledge_index.md"
    click n3 "../modules/knowledge_index.md"
    click n4 "../modules/knowledge_index.md"
    click n5 "../modules/knowledge_index.md"
    click n6 "../modules/knowledge_index.md"
    click n7 "../modules/knowledge_index.md"
    click n8 "../modules/knowledge_links.md"
    click n9 "../modules/knowledge_links.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_links](../modules/knowledge_links.md) | 5 | `external_uri`, `label`, `location`, `normalized_target`, `raw_target`, `resolution`, `resolved_canonical_path`, `source_canonical_path`, `source_locator`, `syntax`, `target_class` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_expected_observation_outcome` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_link_relationship` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_observation_contains_authority_userinfo` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_validate_builder_link` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
| `_validate_observation_endpoint` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_validate_observation_source_syntax` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_validated_observations` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_build_observation` | call | [knowledge_links](../modules/knowledge_links.md) | 1 |
| `_build_observation` | type_reference | [knowledge_links](../modules/knowledge_links.md) | — |
| `collect_link_observations` | type_reference | [knowledge_links](../modules/knowledge_links.md) | — |
