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

An explicit diagnostic request enables the bundled native helper response, validates its selected-path attribution through `native_diagnostics`, and exposes `last_path_outcomes` alongside the inventory. Exact path arguments preserve commas and spaces in filenames. File parse/read failures are distinct from missing helpers and failed batches; no unavailable or failed outcome supplies a parsed module record.

## Imports

| Source | Symbols |
|--------|---------|
| `..services.extractor_helpers` | `ENV_EXTRACTOR_TIMEOUT`, `extractor_timeout_seconds`, `get_prepared_binary`, `missing_helper_message` |
| `..services.go_calls` | `attach_go_receiver_methods` |
| `.common` | `discover_source_files`, `filter_bundled_inventory`, `normalize_include_tests` |
| `.native_diagnostics` | `load_native_chunks`, `path_outcome` |
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
    n2["src/llm_wiki_cli/extractors/native_diagnostics.py"]
    n3["src/llm_wiki_cli/services/extraction_service.py"]
    n4["src/llm_wiki_cli/services/extractor_helpers.py"]
    n5["src/llm_wiki_cli/services/go_calls.py"]
    n1 --> n0
    n1 --> n2
    n1 --> n4
    n1 --> n5
    n2 --> n0
    n3 --> n0
    n3 --> n1
    n3 --> n5
    click n0 "../modules/common.md"
    click n1 "../modules/go_extractor.md"
    click n2 "../modules/native_diagnostics.md"
    click n3 "../modules/extraction_service.md"
    click n4 "../modules/extractor_helpers.md"
    click n5 "../modules/go_calls.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Outbound | [common](../modules/common.md) |
| Outbound | [native_diagnostics](../modules/native_diagnostics.md) |
| Outbound | [extractor_helpers](../modules/extractor_helpers.md) |
| Outbound | [go_calls](../modules/go_calls.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [GoExtractionRequest](../entities/GoExtractionRequest.md) | 39 | — | Internal request object for Go extraction orchestration. |
| [GoExtractor](../entities/GoExtractor.md) | 57 | — | Extractor for Go source files using a prepared helper binary. |