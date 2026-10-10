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
    n0["src/llm_wiki_cli/commands/__init__.py"]
    n1["src/llm_wiki_cli/commands/docs_cmd.py"]
    n2["src/llm_wiki_cli/commands/generate_prompt_cmd.py"]
    n3["src/llm_wiki_cli/commands/hook_cmd.py"]
    n4["src/llm_wiki_cli/commands/init_cmd.py"]
    n5["src/llm_wiki_cli/commands/install_ci_cmd.py"]
    n6["src/llm_wiki_cli/commands/maintenance_cmd.py"]
    n7["src/llm_wiki_cli/commands/migrate_cmd.py"]
    n8["src/llm_wiki_cli/commands/release_cmd.py"]
    n9["src/llm_wiki_cli/commands/sync_cmd.py"]
    n10["src/llm_wiki_cli/commands/trigger_cmd.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n0 --> n4
    n0 --> n5
    n0 --> n6
    n0 --> n7
    n0 --> n8
    n0 --> n9
    n0 --> n10
    n10 --> n2
    click n0 "../modules/commands___init__.md"
    click n1 "../modules/docs_cmd.md"
    click n2 "../modules/generate_prompt_cmd.md"
    click n3 "../modules/hook_cmd.md"
    click n4 "../modules/init_cmd.md"
    click n5 "../modules/install_ci_cmd.md"
    click n6 "../modules/maintenance_cmd.md"
    click n7 "../modules/migrate_cmd.md"
    click n8 "../modules/release_cmd.md"
    click n9 "../modules/sync_cmd.md"
    click n10 "../modules/trigger_cmd.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Outbound | [docs_cmd](../modules/docs_cmd.md) |
| Outbound | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) |
| Outbound | [hook_cmd](../modules/hook_cmd.md) |
| Outbound | [init_cmd](../modules/init_cmd.md) |
| Outbound | [install_ci_cmd](../modules/install_ci_cmd.md) |
| Outbound | [maintenance_cmd](../modules/maintenance_cmd.md) |
| Outbound | [migrate_cmd](../modules/migrate_cmd.md) |
| Outbound | [release_cmd](../modules/release_cmd.md) |
| Outbound | [sync_cmd](../modules/sync_cmd.md) |
| Outbound | [trigger_cmd](../modules/trigger_cmd.md) |
