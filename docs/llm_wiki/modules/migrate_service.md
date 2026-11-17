# migrate_service Module

**Path:** `src/llm_wiki_cli/services/migrate_service.py`

## Description

Typed migrate inputs and results shared by the CLI, the Python API and engines.

Importing this module is cheap; the migration lives in
:mod:`llm_wiki_cli.services.migrate_runtime` and is loaded on first use.

## Imports

| Source | Symbols |
|--------|---------|
| `.path_policy` | `DEFAULT_WIKI_DIR` |
| `__future__` | `annotations` |
| `dataclasses` | `dataclass` |
| `pathlib` | `Path` |
| `typing` | `Any`, `Literal` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/engine/__init__.py"]
    n2["src/llm_wiki_cli/services/migrate_runtime.py"]
    n3["src/llm_wiki_cli/services/migrate_service.py"]
    n4["src/llm_wiki_cli/services/path_policy.py"]
    n0 --> n2
    n0 --> n3
    n1 --> n2
    n1 --> n3
    n2 --> n3
    n3 --> n4
    click n0 "../modules/api.md"
    click n1 "../modules/engine___init__.md"
    click n2 "../modules/migrate_runtime.md"
    click n3 "../modules/migrate_service.md"
    click n4 "../modules/path_policy.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [engine___init__](../modules/engine___init__.md) |
| Inbound | [migrate_runtime](../modules/migrate_runtime.md) |
| Outbound | [path_policy](../modules/path_policy.md) |

## Classes

| Class | Kind | Line | Bases / Target | Description |
|-------|------|------|----------------|-------------|
| [MigrateStatus](../entities/MigrateStatus.md) | Type alias | 15 | `Literal['migrated', 'planned', 'chunk-applied', 'up-to-date']` | — |
| [MigrateRequest](../entities/MigrateRequest.md) | Class | 19 | — | One migration of a wiki written by an older llm-wiki to current naming. |
| [MigrateOutcome](../entities/MigrateOutcome.md) | Class | 40 | — | What one migration did; human-readable progress went to the host streams. |
| [MigrateError](../entities/MigrateError.md) | Class | 71 | `Exception` | Migration stopped; ``exit_code`` is the status the CLI would exit with. |
| [MigrateRequestError](../entities/MigrateRequestError.md) | Class | 79 | `MigrateError` | The request's options are invalid or contradict each other. |
