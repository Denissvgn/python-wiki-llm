# GoExtractor

**Location:** `src/llm_wiki_cli/extractors/go_extractor.py:54`
**Kind:** Class
**Bases:** —
**Module:** [go_extractor](../modules/go_extractor.md)

## Description

Extractor for Go source files using a prepared helper binary.

Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol`.

Each returned file entry includes ``"language": "go"``.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `last_error` | `str \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `extract` | `(src_dir: str \| GoExtractionRequest, only_files: list[str] \| None = None, deep: bool = False) -> dict` | — | Scan Go files and return an inventory dict. |
| `_coerce_request` | `(src_dir: str \| GoExtractionRequest, only_files: list[str] \| None, deep: bool) -> GoExtractionRequest` | — | — |
| `_resolve_source_files` | `(request: GoExtractionRequest) -> list[str]` | — | — |
| `_prepared_helper` | `(request: GoExtractionRequest) -> Path \| None` | — | — |
| `_load_chunked_inventory` | `(request: GoExtractionRequest, source_files: list[str], helper_binary: Path) -> dict` | — | — |
| `_build_command` | `(request: GoExtractionRequest, source_files: list[str], helper_binary: Path) -> list[str]` | — | — |
| `_run_helper` | `(cmd: list[str], helper_binary: Path) -> subprocess.CompletedProcess \| None` | — | — |
| `_load_inventory` | `(result: subprocess.CompletedProcess) -> dict` | — | — |
| `_normalize_inventory` | `(src_dir: str, inventory: dict) -> dict` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
*No generated relationships detected.*

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [go_extractor](../modules/go_extractor.md) | 9 | `last_error` |
