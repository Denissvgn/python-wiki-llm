# rust_extractor Module

**Path:** `src/llm_wiki_cli/extractors/rust_extractor.py`

## Description

Rust AST extractor for agent-wiki-cli.

Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol` by delegating
to a bundled Rust binary (``rust_scripts/src/main.rs``) that uses the ``syn``
crate for Rust AST parsing.

Requirements
------------
* Rust helper prepared with ``llm-wiki prepare-extractors``.

An explicit diagnostic request enables the bundled native helper response, validates its selected-path attribution through `native_diagnostics`, and exposes `last_path_outcomes` alongside the inventory. Exact path arguments preserve commas and spaces in filenames. File parse/read failures are distinct from missing helpers and failed batches; no unavailable or failed outcome supplies a parsed module record.

## Imports

| Source | Symbols |
|--------|---------|
| `..services.extractor_helpers` | `ENV_EXTRACTOR_TIMEOUT`, `extractor_timeout_seconds`, `get_prepared_binary`, `missing_helper_message` |
| `.common` | `discover_source_files`, `filter_bundled_inventory` |
| `.native_diagnostics` | `load_native_chunks`, `path_outcome` |
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
    n1["src/llm_wiki_cli/extractors/native_diagnostics.py"]
    n2["src/llm_wiki_cli/extractors/rust_extractor.py"]
    n3["src/llm_wiki_cli/services/extraction_service.py"]
    n4["src/llm_wiki_cli/services/extractor_helpers.py"]
    n1 --> n0
    n2 --> n0
    n2 --> n1
    n2 --> n4
    n3 --> n0
    n3 --> n2
    click n0 "../modules/common.md"
    click n1 "../modules/native_diagnostics.md"
    click n2 "../modules/rust_extractor.md"
    click n3 "../modules/extraction_service.md"
    click n4 "../modules/extractor_helpers.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Outbound | [common](../modules/common.md) |
| Outbound | [native_diagnostics](../modules/native_diagnostics.md) |
| Outbound | [extractor_helpers](../modules/extractor_helpers.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [RustExtractionRequest](../entities/RustExtractionRequest.md) | 36 | — | Internal request object for Rust extraction orchestration. |
| [RustExtractor](../entities/RustExtractor.md) | 47 | — | Extractor for Rust source files using a prepared helper binary. |