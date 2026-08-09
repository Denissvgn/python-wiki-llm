# AssetIndex

**Location:** `src/llm_wiki_cli/services/wiki_media.py:62`
**Kind:** Class
**Bases:** —
**Module:** [wiki_media](../modules/wiki_media.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `AssetIndex` in `src/llm_wiki_cli/services/wiki_media.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `counts` | `dict[str, object]` | *required* | — |
| `by_page` | `dict[str, list[str]]` | *required* | — |
| `referenced` | `list[str]` | *required* | — |
| `unreferenced` | `list[str]` | *required* | — |
| `expected_pages` | `dict[str, Optional[str]]` | *required* | — |
| `existing_paths` | `frozenset[str]` | `frozenset()` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["AssetIndex (src/llm_wiki_cli/services/wiki_media.py)"]
    n1["build_asset_index (src/llm_wiki_cli/services/wiki_media.py)"]
    n1 --> n0
    click n0 "../modules/wiki_media.md"
    click n1 "../modules/wiki_media.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [wiki_media](../modules/wiki_media.md) | 0 | `by_page`, `counts`, `existing_paths`, `expected_pages`, `referenced`, `unreferenced` |

### References

| Reference | Kind | Source |
|---|---|---|
| `build_asset_index` | call | [wiki_media](../modules/wiki_media.md) |
| `build_asset_index` | type_reference | [wiki_media](../modules/wiki_media.md) |
