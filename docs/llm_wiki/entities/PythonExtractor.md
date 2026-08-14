# PythonExtractor

**Location:** `src/llm_wiki_cli/extractors/python_extractor.py:1528`
**Kind:** Class
**Bases:** —
**Module:** [python_extractor](../modules/python_extractor.md)

## Description

Extractor for Python source files using the built-in :mod:`ast` module.

Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol`.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `() -> None` | — | — |
| `extract` | `(src_dir: str, only_files: list[str] \| None = None, deep: bool = False, include_empty: bool = False, source_files: list[str] \| None = None, capture_data_effect_observations: bool = False, capture_import_observations: bool = False) -> dict` | — | Scan *src_dir* for Python files and return an inventory dict. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
*No generated relationships detected.*

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [python_extractor](../modules/python_extractor.md) | 2 | — |
