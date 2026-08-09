# bump_cmd Module

**Path:** `src/llm_wiki_cli/commands/bump_cmd.py`

## Description

_Auto-generated from `src/llm_wiki_cli/commands/bump_cmd.py`._

## Imports

| Source | Symbols |
|--------|---------|
| `..services.versioning` | `find_version_file`, `read_version`, `write_version`, `bump_patch`, `bump_minor` |
| `subprocess` | `subprocess` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/bump_cmd.py"]
    n2["src/llm_wiki_cli/services/versioning.py"]
    n0 --> n1
    n1 --> n2
    click n0 "../modules/cli.md"
    click n1 "../modules/bump_cmd.md"
    click n2 "../modules/versioning.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [versioning](../modules/versioning.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `run` | `(args)` | — | — |
