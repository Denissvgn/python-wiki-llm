# _ComposeParserState

**Location:** `src/llm_wiki_cli/services/extraction_service.py:2944`
**Kind:** Class
**Bases:** —
**Module:** [extraction_service](../modules/extraction_service.md)

**Decorators:** `@dataclass`

## Description

_Auto-generated from `_ComposeParserState` in `src/llm_wiki_cli/services/extraction_service.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `services` | `dict[str, dict]` | `field(default_factory=dict)` | — |
| `networks` | `list[str]` | `field(default_factory=list)` | — |
| `named_volumes` | `list[str]` | `field(default_factory=list)` | — |
| `current_top` | `str` | `''` | — |
| `current_service` | `str` | `''` | — |
| `key_stack` | `list[str]` | `field(default_factory=list)` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_ComposeParserState (src/llm_wiki_cli/services/extraction_service.py)"]
    n1["_append_compose_list_item (src/llm_wiki_cli/services/extraction_service.py)"]
    n2["_compose_path_parent (src/llm_wiki_cli/services/extraction_service.py)"]
    n3["_parse_compose (src/llm_wiki_cli/services/extraction_service.py)"]
    n4["_parse_compose_service_line (src/llm_wiki_cli/services/extraction_service.py)"]
    n5["_set_compose_service_key (src/llm_wiki_cli/services/extraction_service.py)"]
    n6["_start_compose_service (src/llm_wiki_cli/services/extraction_service.py)"]
    n7["_start_compose_top_level_section (src/llm_wiki_cli/services/extraction_service.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/extraction_service.md"
    click n1 "../modules/extraction_service.md"
    click n2 "../modules/extraction_service.md"
    click n3 "../modules/extraction_service.md"
    click n4 "../modules/extraction_service.md"
    click n5 "../modules/extraction_service.md"
    click n6 "../modules/extraction_service.md"
    click n7 "../modules/extraction_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [extraction_service](../modules/extraction_service.md) | 0 | `current_service`, `current_top`, `key_stack`, `named_volumes`, `networks`, `services` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_append_compose_list_item` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_compose_path_parent` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_parse_compose` | call | [extraction_service](../modules/extraction_service.md) | 1 |
| `_parse_compose_service_line` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_set_compose_service_key` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_start_compose_service` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_start_compose_top_level_section` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
