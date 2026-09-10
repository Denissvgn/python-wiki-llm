# python_imports Module

**Path:** `src/llm_wiki_cli/services/python_imports.py`

## Description

Pure Python import-root indexing over an already selected inventory.

## Imports

| Source | Symbols |
|--------|---------|
| `.python_stdlib` | `python_stdlib_module_names` |
| `__future__` | `annotations` |
| `collections` | `defaultdict` |
| `collections.abc` | `Mapping` |
| `dataclasses` | `dataclass` |
| `pathlib` | `PurePosixPath` |
| `posixpath` | `posixpath` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n1["src/llm_wiki_cli/services/dependencies.py"]
    n2["src/llm_wiki_cli/services/extraction_service.py"]
    n3["src/llm_wiki_cli/services/imports.py"]
    n4["src/llm_wiki_cli/services/packages.py"]
    n5["src/llm_wiki_cli/services/python_imports.py"]
    n6["src/llm_wiki_cli/services/python_stdlib.py"]
    n7["src/llm_wiki_cli/services/relationships.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n0 --> n5
    n0 --> n7
    n1 --> n3
    n1 --> n5
    n1 --> n6
    n2 --> n1
    n2 --> n3
    n2 --> n4
    n2 --> n5
    n3 --> n5
    n4 --> n5
    n5 --> n6
    n7 --> n3
    n7 --> n5
    click n0 "../modules/bootstrap_runtime.md"
    click n1 "../modules/services_dependencies.md"
    click n2 "../modules/extraction_service.md"
    click n3 "../modules/imports.md"
    click n4 "../modules/packages.md"
    click n5 "../modules/python_imports.md"
    click n6 "../modules/python_stdlib.md"
    click n7 "../modules/relationships.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| Inbound | [services_dependencies](../modules/services_dependencies.md) |
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Inbound | [imports](../modules/imports.md) |
| Inbound | [packages](../modules/packages.md) |
| Inbound | [relationships](../modules/relationships.md) |
| Outbound | [python_stdlib](../modules/python_stdlib.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [PythonImportScope](../entities/PythonImportScope.md) | 37 | — | — |
| [PythonModuleIndex](../entities/PythonModuleIndex.md) | 44 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `is_python_source` | `(filepath: str, data: object = None) -> bool` | — | — |
| `normalized_root` | `(value: object) -> str \| None` | — | — |
| `under_root` | `(path: str, root: str) -> bool` | — | — |
| `_relative_target` | `(module: str, importer: str) -> str \| None` | — | — |
