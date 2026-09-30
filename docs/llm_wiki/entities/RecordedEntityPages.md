# _RecordedEntityPages

**Location:** `src/llm_wiki_cli/services/sync_analysis.py:46`
**Kind:** Class
**Bases:** —
**Module:** [sync_analysis](../modules/sync_analysis.md)

**Decorators:** `@dataclass`

## Description

_Auto-generated from `_RecordedEntityPages` in `src/llm_wiki_cli/services/sync_analysis.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `pages` | `dict[EntityOwner, set[str]]` | `field(default_factory=dict)` | — |
| `owners` | `dict[str, set[EntityOwner]]` | `field(default_factory=dict)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `add` | `(owner: EntityOwner, page: object, *, candidate: bool = True) -> None` | — | — |
| `resolve` | `(owner: EntityOwner) -> str \| None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_RecordedEntityPages (src/llm_wiki_cli/services/sync_analysis.py)"]
    n1["_recorded_entity_pages (src/llm_wiki_cli/services/sync_analysis.py)"]
    n1 --> n0
    click n0 "../modules/sync_analysis.md"
    click n1 "../modules/sync_analysis.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_analysis](../modules/sync_analysis.md) | 2 | `owners`, `pages` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_recorded_entity_pages` | call | [sync_analysis](../modules/sync_analysis.md) | 1 |
| `_recorded_entity_pages` | type_reference | [sync_analysis](../modules/sync_analysis.md) | — |
