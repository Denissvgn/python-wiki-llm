# __init__ Module

**Path:** `src/llm_wiki_cli/commands/__init__.py`

## Description

Imports and exposes command modules through the `llm_wiki_cli.commands` package namespace.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `docs_cmd`, `init_cmd`, `extract_cmd`, `lint_cmd`, `hook_cmd`, `install_ci_cmd`, `trigger_cmd`, `generate_prompt_cmd`, `release_cmd`, `sync_cmd`, `migrate_cmd`, `maintenance_cmd` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/__init__.py"]
    n2["src/llm_wiki_cli/commands/docs_cmd.py"]
    n3["src/llm_wiki_cli/commands/generate_prompt_cmd.py"]
    n4["src/llm_wiki_cli/commands/hook_cmd.py"]
    n5["src/llm_wiki_cli/commands/init_cmd.py"]
    n6["src/llm_wiki_cli/commands/install_ci_cmd.py"]
    n7["src/llm_wiki_cli/commands/maintenance_cmd.py"]
    n8["src/llm_wiki_cli/commands/release_cmd.py"]
    n9["src/llm_wiki_cli/commands/trigger_cmd.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n0 --> n5
    n0 --> n6
    n0 --> n7
    n0 --> n8
    n0 --> n9
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n6
    n1 --> n7
    n1 --> n8
    n1 --> n9
    n9 --> n3
    click n0 "../modules/cli.md"
    click n1 "../modules/commands___init__.md"
    click n2 "../modules/docs_cmd.md"
    click n3 "../modules/generate_prompt_cmd.md"
    click n4 "../modules/hook_cmd.md"
    click n5 "../modules/init_cmd.md"
    click n6 "../modules/install_ci_cmd.md"
    click n7 "../modules/maintenance_cmd.md"
    click n8 "../modules/release_cmd.md"
    click n9 "../modules/trigger_cmd.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [docs_cmd](../modules/docs_cmd.md) |
| Outbound | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) |
| Outbound | [hook_cmd](../modules/hook_cmd.md) |
| Outbound | [init_cmd](../modules/init_cmd.md) |
| Outbound | [install_ci_cmd](../modules/install_ci_cmd.md) |
| Outbound | [maintenance_cmd](../modules/maintenance_cmd.md) |
| Outbound | [release_cmd](../modules/release_cmd.md) |
| Outbound | [trigger_cmd](../modules/trigger_cmd.md) |
