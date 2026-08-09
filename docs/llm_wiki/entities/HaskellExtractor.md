# HaskellExtractor

**Location:** `src/llm_wiki_cli/extractors/haskell_extractor.py:36`
**Kind:** Class
**Bases:** —
**Module:** [haskell_extractor](../modules/haskell_extractor.md)

## Description

Extractor for Haskell source files using a prepared helper binary.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `last_error` | `str \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `extract` | `(src_dir: str \| HaskellExtractionRequest, only_files: list[str] \| None = None, deep: bool = False) -> dict` | — | Scan Haskell files and return an inventory dict. |
| `_coerce_request` | `(src_dir: str \| HaskellExtractionRequest, only_files: list[str] \| None, deep: bool) -> HaskellExtractionRequest` | — | — |
| `_resolve_source_files` | `(request: HaskellExtractionRequest) -> list[str]` | — | — |
| `_prepared_helper` | `(request: HaskellExtractionRequest) -> Path \| None` | — | — |
| `_load_chunked_inventory` | `(request: HaskellExtractionRequest, source_files: list[str], helper_binary: Path) -> dict` | — | — |
| `_build_command` | `(request: HaskellExtractionRequest, source_files: list[str], helper_binary: Path) -> list[str]` | — | — |
| `_run_helper` | `(cmd: list[str], helper_binary: Path) -> subprocess.CompletedProcess \| None` | — | — |
| `_load_inventory` | `(result: subprocess.CompletedProcess) -> dict` | — | — |
| `_normalize_inventory` | `(src_dir: str, inventory: dict) -> dict` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
*No generated relationships detected.*

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [haskell_extractor](../modules/haskell_extractor.md) | 9 | `last_error` |
