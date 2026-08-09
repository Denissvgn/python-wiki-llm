# _TsPathAliasRule

**Location:** `src/llm_wiki_cli/services/imports.py:22`
**Kind:** Class
**Bases:** —
**Module:** [imports](../modules/imports.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One ``compilerOptions.paths`` mapping scoped to its tsconfig directory.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `root` | `str` | *required* | — |
| `prefix` | `str` | *required* | — |
| `suffix` | `str` | *required* | — |
| `wildcard` | `bool` | *required* | — |
| `targets` | `tuple[str, ...]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_TsPathAliasRule (src/llm_wiki_cli/services/imports.py)"]
    n1["_match_ts_alias_rule (src/llm_wiki_cli/services/imports.py)"]
    n2["_nearest_ts_alias_root (src/llm_wiki_cli/services/imports.py)"]
    n3["_parse_tsconfig_aliases (src/llm_wiki_cli/services/imports.py)"]
    n4["_read_ts_path_aliases (src/llm_wiki_cli/services/imports.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/imports.md"
    click n1 "../modules/imports.md"
    click n2 "../modules/imports.md"
    click n3 "../modules/imports.md"
    click n4 "../modules/imports.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [imports](../modules/imports.md) | 0 | `prefix`, `root`, `suffix`, `targets`, `wildcard` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_match_ts_alias_rule` | type_reference | [imports](../modules/imports.md) |
| `_nearest_ts_alias_root` | type_reference | [imports](../modules/imports.md) |
| `_parse_tsconfig_aliases` | call | [imports](../modules/imports.md) |
| `_parse_tsconfig_aliases` | type_reference | [imports](../modules/imports.md) |
| `_read_ts_path_aliases` | type_reference | [imports](../modules/imports.md) |
