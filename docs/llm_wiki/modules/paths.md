# paths Module

**Path:** `src/llm_wiki_cli/services/paths.py`

## Description

Shared path normalization helpers.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `pathlib` | `Path`, `PurePosixPath`, `PureWindowsPath` |
| `shlex` | `shlex` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/generate_prompt_cmd.py"]
    n1["src/llm_wiki_cli/commands/hook_cmd.py"]
    n2["src/llm_wiki_cli/commands/migrate_cmd.py"]
    n3["src/llm_wiki_cli/commands/sync_cmd.py"]
    n4["src/llm_wiki_cli/services/api_contracts.py"]
    n5["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n6["src/llm_wiki_cli/services/documentation_native.py"]
    n7["src/llm_wiki_cli/services/paths.py"]
    n8["src/llm_wiki_cli/services/schema.py"]
    n9["src/llm_wiki_cli/services/wiki_surface_index.py"]
    n0 --> n7
    n1 --> n7
    n2 --> n5
    n2 --> n7
    n2 --> n9
    n3 --> n4
    n3 --> n5
    n3 --> n7
    n3 --> n9
    n4 --> n7
    n5 --> n4
    n5 --> n7
    n5 --> n8
    n5 --> n9
    n6 --> n4
    n6 --> n5
    n6 --> n7
    n6 --> n9
    n8 --> n7
    n9 --> n7
    click n0 "../modules/generate_prompt_cmd.md"
    click n1 "../modules/hook_cmd.md"
    click n2 "../modules/migrate_cmd.md"
    click n3 "../modules/sync_cmd.md"
    click n4 "../modules/api_contracts.md"
    click n5 "../modules/bootstrap_runtime.md"
    click n6 "../modules/documentation_native.md"
    click n7 "../modules/paths.md"
    click n8 "../modules/services_schema.md"
    click n9 "../modules/wiki_surface_index.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) |
| Inbound | [hook_cmd](../modules/hook_cmd.md) |
| Inbound | [migrate_cmd](../modules/migrate_cmd.md) |
| Inbound | [sync_cmd](../modules/sync_cmd.md) |
| Inbound | [api_contracts](../modules/api_contracts.md) |
| Inbound | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| Inbound | [documentation_native](../modules/documentation_native.md) |
| Inbound | [services_schema](../modules/services_schema.md) |
| Inbound | [wiki_surface_index](../modules/wiki_surface_index.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `normalize_source_path` | `(value: str \| None, src_dir: str \| None = None) -> str \| None` | — | Normalize a source path from generated markdown or Docker instructions. |
| `is_test_source_path` | `(value: str \| Path \| None) -> bool` | — | Return whether *value* follows a common cross-language test path pattern. |
| `shell_quote` | `(value: str \| Path) -> str` | — | Quote a value for POSIX shell snippets, including Git Bash on Windows. |
| `portable_source_root_label` | `(value: str \| Path, *, base: str \| Path \| None = None) -> str` | — | Return a host-independent source-root label for generated artifacts. |
