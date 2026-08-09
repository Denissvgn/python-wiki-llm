# go_extractor Module

**Path:** `src/llm_wiki_cli/extractors/go_extractor.py`

## Description

Go AST extractor for agent-wiki-cli.

Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol` by delegating
to a bundled Go script (``go_scripts/main.go``) that uses ``go/ast`` and
``go/parser`` for Go AST traversal.

Requirements
------------
* Go helper prepared with ``llm-wiki prepare-extractors``.

## Imports

| Source | Symbols |
|--------|---------|
| `..services.extractor_helpers` | `ENV_EXTRACTOR_TIMEOUT`, `extractor_timeout_seconds`, `get_prepared_binary`, `missing_helper_message` |
| `.common` | `chunk_source_files_for_cli`, `discover_source_files`, `filter_bundled_inventory`, `normalize_include_tests` |
| `__future__` | `annotations` |
| `dataclasses` | `dataclass` |
| `json` | `json` |
| `pathlib` | `Path` |
| `subprocess` | `subprocess` |
| `sys` | `sys` |
| `typing` | `Iterable` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/extractors/common.py"]
    n1["src/llm_wiki_cli/extractors/go_extractor.py"]
    n2["src/llm_wiki_cli/services/extraction_service.py"]
    n3["src/llm_wiki_cli/services/extractor_helpers.py"]
    n1 --> n0
    n1 --> n3
    n2 --> n0
    n2 --> n1
    click n0 "../modules/common.md"
    click n1 "../modules/go_extractor.md"
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
| [GoExtractionRequest](../entities/GoExtractionRequest.md) | 38 | — | Internal request object for Go extraction orchestration. |
| [GoExtractor](../entities/GoExtractor.md) | 54 | — | Extractor for Go source files using a prepared helper binary. |
