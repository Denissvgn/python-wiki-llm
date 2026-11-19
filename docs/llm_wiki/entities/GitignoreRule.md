# _GitignoreRule

**Location:** `src/llm_wiki_engine/gitignore.py:16`
**Kind:** Class
**Bases:** —
**Module:** [gitignore](../modules/gitignore.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_GitignoreRule` in `src/llm_wiki_engine/gitignore.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `base` | `str` | *required* | — |
| `pattern` | `str` | *required* | — |
| `negated` | `bool` | *required* | — |
| `directory_only` | `bool` | *required* | — |
| `anchored` | `bool` | *required* | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_GitignoreRule (src/llm_wiki_engine/gitignore.py)"]
    n1["src/llm_wiki_cli/config.py"]
    n2["_is_root_unanchored_lib_directory_rule (src/llm_wiki_cli/services/source_snapshot.py)"]
    n3["_last_directory_ignore_rule (src/llm_wiki_cli/services/source_snapshot.py)"]
    n4["_parse_gitignore_file (src/llm_wiki_engine/gitignore.py)"]
    n5["_parse_gitignore_text (src/llm_wiki_engine/gitignore.py)"]
    n6["_rule_matches (src/llm_wiki_engine/gitignore.py)"]
    n7["GitIgnoreMatcher.__init__ (src/llm_wiki_engine/gitignore.py)"]
    n8["GitIgnoreMatcher.last_matching_rule (src/llm_wiki_engine/gitignore.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/gitignore.md"
    click n1 "../modules/config.md"
    click n2 "../modules/source_snapshot.md"
    click n3 "../modules/source_snapshot.md"
    click n4 "../modules/gitignore.md"
    click n5 "../modules/gitignore.md"
    click n6 "../modules/gitignore.md"
    click n7 "../modules/gitignore.md"
    click n8 "../modules/gitignore.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [gitignore](../modules/gitignore.md) | 0 | `anchored`, `base`, `directory_only`, `negated`, `pattern` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `config` | import | [config](../modules/config.md) | — |
| `_is_root_unanchored_lib_directory_rule` | type_reference | [source_snapshot](../modules/source_snapshot.md) | — |
| `_last_directory_ignore_rule` | type_reference | [source_snapshot](../modules/source_snapshot.md) | — |
| `_parse_gitignore_file` | type_reference | [gitignore](../modules/gitignore.md) | — |
| `_parse_gitignore_text` | call | [gitignore](../modules/gitignore.md) | 1 |
| `_parse_gitignore_text` | type_reference | [gitignore](../modules/gitignore.md) | — |
| `_rule_matches` | type_reference | [gitignore](../modules/gitignore.md) | — |
| `GitIgnoreMatcher.__init__` | type_reference | [gitignore](../modules/gitignore.md) | — |
| `GitIgnoreMatcher.last_matching_rule` | type_reference | [gitignore](../modules/gitignore.md) | — |
