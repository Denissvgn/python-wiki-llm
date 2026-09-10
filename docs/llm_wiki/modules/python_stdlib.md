# python_stdlib Module

**Path:** `src/llm_wiki_cli/services/python_stdlib.py`

## Description

Shared, interpreter-compatible Python standard-library module names.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/dependencies.py"]
    n1["src/llm_wiki_cli/services/python_imports.py"]
    n2["src/llm_wiki_cli/services/python_stdlib.py"]
    n0 --> n1
    n0 --> n2
    n1 --> n2
    click n0 "../modules/services_dependencies.md"
    click n1 "../modules/python_imports.md"
    click n2 "../modules/python_stdlib.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [services_dependencies](../modules/services_dependencies.md) |
| Inbound | [python_imports](../modules/python_imports.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `python_stdlib_module_names` | `() -> frozenset[str]` | — | — |
