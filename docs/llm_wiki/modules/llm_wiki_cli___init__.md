# __init__ Module

**Path:** `src/llm_wiki_cli/__init__.py`

## Description

LLM Wiki CLI.

## Imports

| Source | Symbols |
|--------|---------|
| `importlib.metadata` | `version`, `PackageNotFoundError` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/__init__.py"]
    n1["src/llm_wiki_cli/cli.py"]
    n2["src/llm_wiki_cli/commands/migrate_cmd.py"]
    n3["src/llm_wiki_cli/commands/sync_cmd.py"]
    n4["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n5["src/llm_wiki_cli/services/context_packet.py"]
    n6["src/llm_wiki_cli/services/documentation_run/dependencies.py"]
    n7["src/llm_wiki_cli/services/inventory_cache.py"]
    n8["src/llm_wiki_cli/services/knowledge_orchestration.py"]
    n9["src/llm_wiki_cli/services/plugins.py"]
    n1 --> n0
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n2 --> n0
    n2 --> n4
    n2 --> n8
    n3 --> n0
    n3 --> n4
    n3 --> n7
    n3 --> n8
    n3 --> n9
    n4 --> n0
    n4 --> n8
    n5 --> n0
    n5 --> n9
    n6 --> n0
    n7 --> n0
    n7 --> n9
    n8 --> n0
    n9 --> n0
    click n0 "../modules/llm_wiki_cli___init__.md"
    click n1 "../modules/cli.md"
    click n2 "../modules/migrate_cmd.md"
    click n3 "../modules/sync_cmd.md"
    click n4 "../modules/bootstrap_runtime.md"
    click n5 "../modules/context_packet.md"
    click n6 "../modules/documentation_run_dependencies.md"
    click n7 "../modules/inventory_cache.md"
    click n8 "../modules/knowledge_orchestration.md"
    click n9 "../modules/plugins.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Inbound | [migrate_cmd](../modules/migrate_cmd.md) |
| Inbound | [sync_cmd](../modules/sync_cmd.md) |
| Inbound | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| Inbound | [context_packet](../modules/context_packet.md) |
| Inbound | [documentation_run_dependencies](../modules/documentation_run_dependencies.md) |
| Inbound | [inventory_cache](../modules/inventory_cache.md) |
| Inbound | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| Inbound | [plugins](../modules/plugins.md) |
