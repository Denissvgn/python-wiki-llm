# hook_cmd Module

**Path:** `src/llm_wiki_cli/commands/hook_cmd.py`

## Description

_Auto-generated from `src/llm_wiki_cli/commands/hook_cmd.py`._

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `DEFAULT_WIKI_DIR`, `get_agent_config_path`, `read_config`, `validate_path`, `write_config` |
| `..services.paths` | `shell_quote` |
| `..services.source_selection` | `SourceSelectionError`, `resolve_source_selection` |
| `__future__` | `annotations` |
| `os` | `os` |
| `pathlib` | `Path` |
| `stat` | `stat` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/hook_cmd.py"]
    n2["src/llm_wiki_cli/commands/upgrade_cmd.py"]
    n3["src/llm_wiki_cli/config.py"]
    n4["src/llm_wiki_cli/services/paths.py"]
    n5["src/llm_wiki_cli/services/source_selection.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n2 --> n1
    n2 --> n3
    n2 --> n5
    n5 --> n3
    click n0 "../modules/cli.md"
    click n1 "../modules/hook_cmd.md"
    click n2 "../modules/upgrade_cmd.md"
    click n3 "../modules/config.md"
    click n4 "../modules/paths.md"
    click n5 "../modules/source_selection.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Inbound | [upgrade_cmd](../modules/upgrade_cmd.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [paths](../modules/paths.md) |
| Outbound | [source_selection](../modules/source_selection.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_read_agent_config` | `(wiki_dir: str) -> str \| None` | — | Read the agent name persisted by `llm-wiki init`. |
| `_build_post_commit` | `(agent: str, wiki_dir: str, source_selection: str \| Path \| None = None) -> str` | — | Build the managed post-commit hook. |
| `_build_ide_post_commit` | `(wiki_dir: str, *, source_selection: str \| Path \| None = None) -> str` | — | — |
| `_build_validation_pre_commit` | `(wiki_dir: str, *, source_selection: str \| Path \| None = None) -> str` | — | — |
| `_source_selection_args` | `(source_selection: str \| Path \| None) -> str` | — | — |
| `_install_hook` | `(hooks_dir: Path, name: str, content: str, *, force: bool = False) -> None` | — | Write a hook file and make it executable. |
| `run` | `(args)` | — | — |
