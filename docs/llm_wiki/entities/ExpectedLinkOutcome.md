# _ExpectedLinkOutcome

**Location:** `src/llm_wiki_cli/services/knowledge_index.py:204`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_index](../modules/knowledge_index.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_ExpectedLinkOutcome` in `src/llm_wiki_cli/services/knowledge_index.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `target_class` | `TargetClass` | *required* | — |
| `resolution` | `Resolution \| None` | *required* | — |
| `canonical_path` | `str \| None` | `None` | — |
| `external_uri` | `str \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_ExpectedLinkOutcome (src/llm_wiki_cli/services/knowledge_index.py)"]
    n1["_expected_observation_outcome (src/llm_wiki_cli/services/knowledge_index.py)"]
    n1 --> n0
    click n0 "../modules/knowledge_index.md"
    click n1 "../modules/knowledge_index.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_index](../modules/knowledge_index.md) | 0 | `canonical_path`, `external_uri`, `resolution`, `target_class` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_expected_observation_outcome` | call | [knowledge_index](../modules/knowledge_index.md) | 14 |
| `_expected_observation_outcome` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
