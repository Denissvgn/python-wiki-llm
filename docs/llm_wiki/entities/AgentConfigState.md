# AgentConfigState

**Location:** `src/llm_wiki_cli/config.py:313`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [config](../modules/config.md)

## Description

Compatibility classification for the local agent configuration.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `ABSENT` | `'absent'` | — |
| `VALID` | `'valid'` | — |
| `LEGACY` | `'legacy'` | — |
| `INVALID` | `'invalid'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["AgentConfigState (src/llm_wiki_cli/config.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/commands/hook_cmd.py"]
    n4["src/llm_wiki_cli/commands/init_cmd.py"]
    n5["src/llm_wiki_cli/commands/status_cmd.py"]
    n6["src/llm_wiki_cli/commands/upgrade_cmd.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/config.md"
    click n3 "../modules/hook_cmd.md"
    click n4 "../modules/init_cmd.md"
    click n5 "../modules/status_cmd.md"
    click n6 "../modules/upgrade_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [config](../modules/config.md) | 0 | `ABSENT`, `INVALID`, `LEGACY`, `VALID` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `hook_cmd` | import | [hook_cmd](../modules/hook_cmd.md) | — |
| `init_cmd` | import | [init_cmd](../modules/init_cmd.md) | — |
| `status_cmd` | import | [status_cmd](../modules/status_cmd.md) | — |
| `upgrade_cmd` | import | [upgrade_cmd](../modules/upgrade_cmd.md) | — |
