# python_imports Module

**Path:** `src/llm_wiki_cli/services/python_imports.py`

## Description

Python import roots and captured module bindings over selected inventory.

Separates module-root resolution from module namespace authority. Captured Python binding facts select matching imports for alias consumers, while dependency analysis retains all lexical imports. Inventories without binding capture retain their existing import-based compatibility fallback; that fallback does not establish live namespace correctness.

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
    n0["src/llm_wiki_cli/extractors/python_contracts.py"]
    n1["src/llm_wiki_cli/services/api_contracts.py"]
    n2["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n3["src/llm_wiki_cli/services/dependencies.py"]
    n4["src/llm_wiki_cli/services/entrypoints.py"]
    n5["src/llm_wiki_cli/services/extraction_service.py"]
    n6["src/llm_wiki_cli/services/imports.py"]
    n7["src/llm_wiki_cli/services/packages.py"]
    n8["src/llm_wiki_cli/services/python_imports.py"]
    n9["src/llm_wiki_cli/services/python_stdlib.py"]
    n10["src/llm_wiki_cli/services/relationships.py"]
    n0 --> n8
    n1 --> n6
    n1 --> n8
    n2 --> n1
    n2 --> n3
    n2 --> n4
    n2 --> n5
    n2 --> n6
    n2 --> n8
    n2 --> n10
    n3 --> n6
    n3 --> n8
    n3 --> n9
    n4 --> n6
    n4 --> n8
    n5 --> n0
    n5 --> n1
    n5 --> n3
    n5 --> n4
    n5 --> n6
    n5 --> n7
    n5 --> n8
    n6 --> n7
    n6 --> n8
    n7 --> n8
    n8 --> n9
    n10 --> n6
    n10 --> n8
    click n0 "../modules/python_contracts.md"
    click n1 "../modules/api_contracts.md"
    click n2 "../modules/bootstrap_runtime.md"
    click n3 "../modules/services_dependencies.md"
    click n4 "../modules/entrypoints.md"
    click n5 "../modules/extraction_service.md"
    click n6 "../modules/imports.md"
    click n7 "../modules/packages.md"
    click n8 "../modules/python_imports.md"
    click n9 "../modules/python_stdlib.md"
    click n10 "../modules/relationships.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [python_contracts](../modules/python_contracts.md) |
| Inbound | [api_contracts](../modules/api_contracts.md) |
| Inbound | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| Inbound | [services_dependencies](../modules/services_dependencies.md) |
| Inbound | [entrypoints](../modules/entrypoints.md) |
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Inbound | [imports](../modules/imports.md) |
| Inbound | [packages](../modules/packages.md) |
| Inbound | [relationships](../modules/relationships.md) |
| Outbound | [python_stdlib](../modules/python_stdlib.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [PythonImportScope](../entities/PythonImportScope.md) | 63 | — | — |
| [PythonModuleIndex](../entities/PythonModuleIndex.md) | 70 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `module_binding_imports` | `(file_data: Mapping) -> list[dict]` | — | Dependency imports imply module aliases only with matching binding facts. |
| `is_python_source` | `(filepath: str, data: object = None) -> bool` | — | — |
| `normalized_root` | `(value: object) -> str \| None` | — | — |
| `under_root` | `(path: str, root: str) -> bool` | — | — |
| `_relative_target` | `(module: str, importer: str) -> str \| None` | — | — |
