# HaskellExtractionRequest

**Location:** `src/llm_wiki_cli/extractors/haskell_extractor.py:26`
**Kind:** Class
**Bases:** —
**Module:** [haskell_extractor](../modules/haskell_extractor.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Internal request object for Haskell extraction orchestration.

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
    n0["HaskellExtractionRequest (src/llm_wiki_cli/extractors/haskell_extractor.py)"]
    n1["_missing_haskell_helper_message (src/llm_wiki_cli/extractors/haskell_extractor.py)"]
    n2["HaskellExtractor._build_command (src/llm_wiki_cli/extractors/haskell_extractor.py)"]
    n3["HaskellExtractor._coerce_request (src/llm_wiki_cli/extractors/haskell_extractor.py)"]
    n4["HaskellExtractor._load_chunked_inventory (src/llm_wiki_cli/extractors/haskell_extractor.py)"]
    n5["HaskellExtractor._prepared_helper (src/llm_wiki_cli/extractors/haskell_extractor.py)"]
    n6["HaskellExtractor._resolve_source_files (src/llm_wiki_cli/extractors/haskell_extractor.py)"]
    n7["HaskellExtractor.extract (src/llm_wiki_cli/extractors/haskell_extractor.py)"]
    n8["_build_builtin_extraction_kwargs (src/llm_wiki_cli/services/extraction_service.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/haskell_extractor.md"
    click n1 "../modules/haskell_extractor.md"
    click n2 "../modules/haskell_extractor.md"
    click n3 "../modules/haskell_extractor.md"
    click n4 "../modules/haskell_extractor.md"
    click n5 "../modules/haskell_extractor.md"
    click n6 "../modules/haskell_extractor.md"
    click n7 "../modules/haskell_extractor.md"
    click n8 "../modules/extraction_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [haskell_extractor](../modules/haskell_extractor.md) | 0 | `deep`, `helper_cache_dir`, `only_files`, `source_files`, `src_dir` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_missing_haskell_helper_message` | type_reference | [haskell_extractor](../modules/haskell_extractor.md) |
| `HaskellExtractor._build_command` | type_reference | [haskell_extractor](../modules/haskell_extractor.md) |
| `HaskellExtractor._coerce_request` | call | [haskell_extractor](../modules/haskell_extractor.md) |
| `HaskellExtractor._coerce_request` | type_reference | [haskell_extractor](../modules/haskell_extractor.md) |
| `HaskellExtractor._load_chunked_inventory` | type_reference | [haskell_extractor](../modules/haskell_extractor.md) |
| `HaskellExtractor._prepared_helper` | type_reference | [haskell_extractor](../modules/haskell_extractor.md) |
| `HaskellExtractor._resolve_source_files` | type_reference | [haskell_extractor](../modules/haskell_extractor.md) |
| `HaskellExtractor.extract` | type_reference | [haskell_extractor](../modules/haskell_extractor.md) |
| `_build_builtin_extraction_kwargs` | call | [extraction_service](../modules/extraction_service.md) |
