# LegacyHookError

**Location:** `src/llm_wiki_cli/services/legacy_hooks.py:24`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [legacy_hooks](../modules/legacy_hooks.md)

## Description

Hook ownership or its filesystem snapshot cannot be verified safely.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["LegacyHookError (src/llm_wiki_cli/services/legacy_hooks.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/commands/status_cmd.py"]
    n3["src/llm_wiki_cli/commands/uninstall_cmd.py"]
    n4["src/llm_wiki_cli/commands/upgrade_cmd.py"]
    n5["_git_value (src/llm_wiki_cli/services/legacy_hooks.py)"]
    n6["_hook_directories (src/llm_wiki_cli/services/legacy_hooks.py)"]
    n7["_require_safe_path (src/llm_wiki_cli/services/legacy_hooks.py)"]
    n8["inspect_legacy_hooks (src/llm_wiki_cli/services/legacy_hooks.py)"]
    n9["remove_legacy_hooks (src/llm_wiki_cli/services/legacy_hooks.py)"]
    n10["src/llm_wiki_cli/services/mcp_server.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    click n0 "../modules/legacy_hooks.md"
    click n2 "../modules/status_cmd.md"
    click n3 "../modules/uninstall_cmd.md"
    click n4 "../modules/upgrade_cmd.md"
    click n5 "../modules/legacy_hooks.md"
    click n6 "../modules/legacy_hooks.md"
    click n7 "../modules/legacy_hooks.md"
    click n8 "../modules/legacy_hooks.md"
    click n9 "../modules/legacy_hooks.md"
    click n10 "../modules/mcp_server.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [legacy_hooks](../modules/legacy_hooks.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `status_cmd` | import | [status_cmd](../modules/status_cmd.md) | — |
| `uninstall_cmd` | import | [uninstall_cmd](../modules/uninstall_cmd.md) | — |
| `upgrade_cmd` | import | [upgrade_cmd](../modules/upgrade_cmd.md) | — |
| `_git_value` | call | [legacy_hooks](../modules/legacy_hooks.md) | 3 |
| `_hook_directories` | call | [legacy_hooks](../modules/legacy_hooks.md) | 2 |
| `_require_safe_path` | call | [legacy_hooks](../modules/legacy_hooks.md) | 1 |
| `inspect_legacy_hooks` | call | [legacy_hooks](../modules/legacy_hooks.md) | 3 |
| `remove_legacy_hooks` | call | [legacy_hooks](../modules/legacy_hooks.md) | 2 |
| `mcp_server` | import | [mcp_server](../modules/mcp_server.md) | — |
