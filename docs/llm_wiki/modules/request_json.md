# request_json Module

**Path:** `src/llm_wiki_cli/services/request_json.py`

## Description

Loads explicit JSON request files or stdin under a one-mebibyte UTF-8 bound. Duplicate keys, nonfinite numbers, malformed text and non-object requests fail before the request reaches workspace readers.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `json` | `json` |
| `pathlib` | `Path` |
| `sys` | `sys` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/request_json.py"]
    n0 --> n1
    click n1 "../modules/request_json.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (12) |

> All 12 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_pairs` | `(items)` | — | — |
| `_constant` | `(value)` | — | — |
| `parse_request` | `(raw: bytes \| str) -> dict[str, Any]` | — | — |
| `load_request` | `(path: str) -> dict[str, Any]` | — | — |