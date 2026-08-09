# haskell_extractor Module

**Path:** `src/llm_wiki_cli/extractors/haskell_extractor.py`

## Description

Haskell source extractor backed by a prepared helper binary.

## Imports

| Source | Symbols |
|--------|---------|
| `..services.extractor_helpers` | `ENV_EXTRACTOR_TIMEOUT`, `extractor_timeout_seconds`, `get_prepared_binary` |
| `.common` | `chunk_source_files_for_cli`, `discover_source_files`, `filter_bundled_inventory` |
| `__future__` | `annotations` |
| `dataclasses` | `dataclass` |
| `json` | `json` |
| `pathlib` | `Path` |
| `subprocess` | `subprocess` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/extractors/common.py"]
    n1["src/llm_wiki_cli/extractors/haskell_extractor.py"]
    n2["src/llm_wiki_cli/services/extraction_service.py"]
    n3["src/llm_wiki_cli/services/extractor_helpers.py"]
    n1 --> n0
    n1 --> n3
    n2 --> n0
    n2 --> n1
    click n0 "../modules/common.md"
    click n1 "../modules/haskell_extractor.md"
    click n2 "../modules/extraction_service.md"
    click n3 "../modules/extractor_helpers.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Outbound | [common](../modules/common.md) |
| Outbound | [extractor_helpers](../modules/extractor_helpers.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [HaskellExtractionRequest](../entities/HaskellExtractionRequest.md) | 26 | — | Internal request object for Haskell extraction orchestration. |
| [HaskellExtractor](../entities/HaskellExtractor.md) | 36 | — | Extractor for Haskell source files using a prepared helper binary. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_missing_haskell_helper_message` | `(request: HaskellExtractionRequest) -> str` | — | — |
| `_normalize_inventory_path` | `(src_root: Path, raw_path: str) -> str` | — | — |
