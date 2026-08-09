# install_ci_cmd Module

**Path:** `src/llm_wiki_cli/commands/install_ci_cmd.py`

## Description

CLI adapter for installing the portable LLM Wiki integrity workflow.

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `DEFAULT_WIKI_DIR` |
| `..services.ci_installer` | `InstallCiError`, `install_ci_workflow` |
| `__future__` | `annotations` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/install_ci_cmd.py"]
    n2["src/llm_wiki_cli/config.py"]
    n3["src/llm_wiki_cli/services/ci_installer.py"]
    n0 --> n1
    n0 --> n2
    n1 --> n2
    n1 --> n3
    click n0 "../modules/cli.md"
    click n1 "../modules/install_ci_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/ci_installer.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [ci_installer](../modules/ci_installer.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `run` | `(args) -> None` | — | — |
