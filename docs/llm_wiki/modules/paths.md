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
    n3["src/llm_wiki_cli/commands/status_cmd.py"]
    n4["src/llm_wiki_cli/commands/sync_cmd.py"]
    n5["src/llm_wiki_cli/commands/uninstall_cmd.py"]
    n6["src/llm_wiki_cli/services/api_contracts.py"]
    n7["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n8["src/llm_wiki_cli/services/documentation_native.py"]
    n9["src/llm_wiki_cli/services/paths.py"]
    n10["src/llm_wiki_cli/services/schema.py"]
    n11["src/llm_wiki_cli/services/wiki_surface_index.py"]
    n0 --> n9
    n1 --> n9
    n2 --> n7
    n2 --> n9
    n2 --> n11
    n3 --> n1
    n3 --> n9
    n3 --> n10
    n4 --> n6
    n4 --> n7
    n4 --> n9
    n4 --> n11
    n5 --> n1
    n5 --> n9
    n5 --> n10
    n6 --> n9
    n7 --> n6
    n7 --> n9
    n7 --> n10
    n7 --> n11
    n8 --> n6
    n8 --> n7
    n8 --> n9
    n8 --> n11
    n10 --> n9
    n11 --> n9
    click n0 "../modules/generate_prompt_cmd.md"
    click n1 "../modules/hook_cmd.md"
    click n2 "../modules/migrate_cmd.md"
    click n3 "../modules/status_cmd.md"
    click n4 "../modules/sync_cmd.md"
    click n5 "../modules/uninstall_cmd.md"
    click n6 "../modules/api_contracts.md"
    click n7 "../modules/bootstrap_runtime.md"
    click n8 "../modules/documentation_native.md"
    click n9 "../modules/paths.md"
    click n10 "../modules/services_schema.md"
    click n11 "../modules/wiki_surface_index.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) |
| Inbound | [hook_cmd](../modules/hook_cmd.md) |
| Inbound | [migrate_cmd](../modules/migrate_cmd.md) |
| Inbound | [status_cmd](../modules/status_cmd.md) |
| Inbound | [sync_cmd](../modules/sync_cmd.md) |
| Inbound | [uninstall_cmd](../modules/uninstall_cmd.md) |
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
| `display_project_path` | `(path: Path) -> str` | — | Render a checkout-local path with stable POSIX separators. |
| `portable_source_root_label` | `(value: str \| Path, *, base: str \| Path \| None = None) -> str` | — | Return a host-independent source-root label for generated artifacts. |
