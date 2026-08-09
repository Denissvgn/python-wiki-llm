# RustExtractionRequest

**Location:** `src/llm_wiki_cli/extractors/rust_extractor.py:36`
**Kind:** Class
**Bases:** —
**Module:** [rust_extractor](../modules/rust_extractor.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Internal request object for Rust extraction orchestration.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `src_dir` | `str` | *required* | — |
| `only_files` | `list[str] \| None` | `None` | — |
| `deep` | `bool` | `False` | — |
| `source_files` | `list[str] \| None` | `None` | — |
| `helper_cache_dir` | `str \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["RustExtractionRequest (src/llm_wiki_cli/extractors/rust_extractor.py)"]
    n1["RustExtractor._build_command (src/llm_wiki_cli/extractors/rust_extractor.py)"]
    n2["RustExtractor._coerce_request (src/llm_wiki_cli/extractors/rust_extractor.py)"]
    n3["RustExtractor._load_chunked_inventory (src/llm_wiki_cli/extractors/rust_extractor.py)"]
    n4["RustExtractor._prepared_helper (src/llm_wiki_cli/extractors/rust_extractor.py)"]
    n5["RustExtractor._resolve_source_files (src/llm_wiki_cli/extractors/rust_extractor.py)"]
    n6["RustExtractor.extract (src/llm_wiki_cli/extractors/rust_extractor.py)"]
    n7["_build_builtin_extraction_kwargs (src/llm_wiki_cli/services/extraction_service.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/rust_extractor.md"
    click n1 "../modules/rust_extractor.md"
    click n2 "../modules/rust_extractor.md"
    click n3 "../modules/rust_extractor.md"
    click n4 "../modules/rust_extractor.md"
    click n5 "../modules/rust_extractor.md"
    click n6 "../modules/rust_extractor.md"
    click n7 "../modules/extraction_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [rust_extractor](../modules/rust_extractor.md) | 0 | `deep`, `helper_cache_dir`, `only_files`, `source_files`, `src_dir` |

### References

| Reference | Kind | Source |
|---|---|---|
| `RustExtractor._build_command` | type_reference | [rust_extractor](../modules/rust_extractor.md) |
| `RustExtractor._coerce_request` | call | [rust_extractor](../modules/rust_extractor.md) |
| `RustExtractor._coerce_request` | type_reference | [rust_extractor](../modules/rust_extractor.md) |
| `RustExtractor._load_chunked_inventory` | type_reference | [rust_extractor](../modules/rust_extractor.md) |
| `RustExtractor._prepared_helper` | type_reference | [rust_extractor](../modules/rust_extractor.md) |
| `RustExtractor._resolve_source_files` | type_reference | [rust_extractor](../modules/rust_extractor.md) |
| `RustExtractor.extract` | type_reference | [rust_extractor](../modules/rust_extractor.md) |
| `_build_builtin_extraction_kwargs` | call | [extraction_service](../modules/extraction_service.md) |
