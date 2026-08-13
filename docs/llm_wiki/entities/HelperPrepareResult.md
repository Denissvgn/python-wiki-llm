# HelperPrepareResult

**Location:** `src/llm_wiki_cli/services/extractor_helpers.py:43`
**Kind:** Class
**Bases:** —
**Module:** [extractor_helpers](../modules/extractor_helpers.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `HelperPrepareResult` in `src/llm_wiki_cli/services/extractor_helpers.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `language` | `str` | *required* | — |
| `status` | `str` | *required* | — |
| `message` | `str` | *required* | — |
| `path` | `str \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["HelperPrepareResult (src/llm_wiki_cli/services/extractor_helpers.py)"]
    n1["_format_result (src/llm_wiki_cli/commands/prepare_extractors_cmd.py)"]
    n2["prepare_go (src/llm_wiki_cli/services/extractor_helpers.py)"]
    n3["prepare_haskell (src/llm_wiki_cli/services/extractor_helpers.py)"]
    n4["prepare_helper (src/llm_wiki_cli/services/extractor_helpers.py)"]
    n5["prepare_rust (src/llm_wiki_cli/services/extractor_helpers.py)"]
    n6["prepare_typescript (src/llm_wiki_cli/services/extractor_helpers.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/extractor_helpers.md"
    click n1 "../modules/prepare_extractors_cmd.md"
    click n2 "../modules/extractor_helpers.md"
    click n3 "../modules/extractor_helpers.md"
    click n4 "../modules/extractor_helpers.md"
    click n5 "../modules/extractor_helpers.md"
    click n6 "../modules/extractor_helpers.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [extractor_helpers](../modules/extractor_helpers.md) | 0 | `language`, `message`, `path`, `status` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_format_result` | type_reference | [prepare_extractors_cmd](../modules/prepare_extractors_cmd.md) | — |
| `prepare_go` | call | [extractor_helpers](../modules/extractor_helpers.md) | 8 |
| `prepare_go` | type_reference | [extractor_helpers](../modules/extractor_helpers.md) | — |
| `prepare_haskell` | call | [extractor_helpers](../modules/extractor_helpers.md) | 9 |
| `prepare_haskell` | type_reference | [extractor_helpers](../modules/extractor_helpers.md) | — |
| `prepare_helper` | call | [extractor_helpers](../modules/extractor_helpers.md) | 1 |
| `prepare_helper` | type_reference | [extractor_helpers](../modules/extractor_helpers.md) | — |
| `prepare_rust` | call | [extractor_helpers](../modules/extractor_helpers.md) | 6 |
| `prepare_rust` | type_reference | [extractor_helpers](../modules/extractor_helpers.md) | — |
| `prepare_typescript` | call | [extractor_helpers](../modules/extractor_helpers.md) | 9 |
| `prepare_typescript` | type_reference | [extractor_helpers](../modules/extractor_helpers.md) | — |
