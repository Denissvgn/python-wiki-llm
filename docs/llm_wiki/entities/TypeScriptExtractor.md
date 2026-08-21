# TypeScriptExtractor

**Location:** `src/llm_wiki_cli/extractors/ts_extractor.py:38`
**Kind:** Class
**Bases:** —
**Module:** [ts_extractor](../modules/ts_extractor.md)

## Description

Extractor for TypeScript source files using a Node.js/ts-morph subprocess.

Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol`.

Each returned file entry includes ``"language": "typescript"`` for
``.ts``/``.tsx`` files or ``"language": "javascript"`` for
``.js``/``.jsx`` files.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `last_error` | `str \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `extract` | `(src_dir: str, only_files: list[str] \| None = None, deep: bool = False, source_files: list[str] \| None = None, helper_cache_dir: str \| None = None) -> dict` | — | Scan *src_dir* for TypeScript files and return an inventory dict. |
| `_resolve_source_files` | `(src_dir: str, only_files: list[str] \| None, source_files: list[str] \| None) -> list[str]` | — | — |
| `_toolchain_root` | `(src_dir: str, helper_cache_dir: str \| None = None) -> Path \| None` | — | — |
| `_build_command` | `(src_dir: str, source_files: list[str], deep: bool, helper_root: Path) -> list[str]` | — | — |
| `_run_node_extractor` | `(cmd: list[str], helper_root: Path) -> subprocess.CompletedProcess \| None` | — | — |
| `_load_inventory` | `(result: subprocess.CompletedProcess) -> dict` | — | — |
| `_normalize_inventory` | `(src_dir: str, inventory: dict, helper_root: Path) -> dict` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
*No generated relationships detected.*

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [ts_extractor](../modules/ts_extractor.md) | 7 | `last_error` |
