# PathValidationError

**Location:** `src/llm_wiki_cli/config.py:121`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [config](../modules/config.md)

## Description

Raised when a user-provided path escapes the project root.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PathValidationError (src/llm_wiki_cli/config.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/api.py"]
    n3["src/llm_wiki_cli/cli.py"]
    n4["src/llm_wiki_cli/commands/docs_cmd.py"]
    n5["src/llm_wiki_cli/commands/upgrade_cmd.py"]
    n6["require_committed_config (src/llm_wiki_cli/config.py)"]
    n7["require_config_inspection_unchanged (src/llm_wiki_cli/config.py)"]
    n8["require_safe_config_path (src/llm_wiki_cli/config.py)"]
    n9["validate_path (src/llm_wiki_cli/config.py)"]
    n10["validate_source_paths (src/llm_wiki_cli/config.py)"]
    n11["validate_source_root (src/llm_wiki_cli/config.py)"]
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
    n11 --> n0
    click n0 "../modules/config.md"
    click n2 "../modules/api.md"
    click n3 "../modules/cli.md"
    click n4 "../modules/docs_cmd.md"
    click n5 "../modules/upgrade_cmd.md"
    click n6 "../modules/config.md"
    click n7 "../modules/config.md"
    click n8 "../modules/config.md"
    click n9 "../modules/config.md"
    click n10 "../modules/config.md"
    click n11 "../modules/config.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [config](../modules/config.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `api` | import | [api](../modules/api.md) |
| `cli` | import | [cli](../modules/cli.md) |
| `docs_cmd` | import | [docs_cmd](../modules/docs_cmd.md) |
| `upgrade_cmd` | import | [upgrade_cmd](../modules/upgrade_cmd.md) |
| `require_committed_config` | call | [config](../modules/config.md) |
| `require_config_inspection_unchanged` | call | [config](../modules/config.md) |
| `require_safe_config_path` | call | [config](../modules/config.md) |
| `require_safe_config_path` | call | [config](../modules/config.md) |
| `validate_path` | call | [config](../modules/config.md) |
| `validate_path` | call | [config](../modules/config.md) |
| `validate_source_paths` | call | [config](../modules/config.md) |
| `validate_source_root` | call | [config](../modules/config.md) |
