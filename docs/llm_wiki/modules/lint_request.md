# lint_request Module

**Path:** `src/llm_wiki_cli/services/lint_request.py`

## Description

Typed lint inputs shared by the CLI, the Python API and engines.

Importing this module is cheap; the checks live in
:mod:`llm_wiki_cli.services.lint_service` and are loaded on first use.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `collections.abc` | `Iterable` |
| `dataclasses` | `dataclass` |
| `llm_wiki_engine.path_policy` | `DEFAULT_WIKI_DIR` |
| `pathlib` | `Path` |
| `typing` | `Literal` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/engine/__init__.py"]
    n2["src/llm_wiki_cli/services/lint_request.py"]
    n3["src/llm_wiki_cli/services/lint_service.py"]
    n4["src/llm_wiki_engine/path_policy.py"]
    n0 --> n2
    n0 --> n3
    n1 --> n2
    n1 --> n3
    n2 --> n4
    n3 --> n2
    n3 --> n4
    click n0 "../modules/api.md"
    click n1 "../modules/engine___init__.md"
    click n2 "../modules/lint_request.md"
    click n3 "../modules/lint_service.md"
    click n4 "../modules/path_policy.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [engine___init__](../modules/engine___init__.md) |
| Inbound | [lint_service](../modules/lint_service.md) |
| Outbound | [path_policy](../modules/path_policy.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [LintRequest](../entities/lint_request_LintRequest.md) | 18 | — | One lint of ``wiki_root`` against ``source_root``. |
| [LintRequestError](../entities/LintRequestError.md) | 45 | `ValueError` | The lint request names a path the workspace policy rejects. |
