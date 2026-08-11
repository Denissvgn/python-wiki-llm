# ManagedSchemaBlockState

**Location:** `src/llm_wiki_cli/services/schema.py:34`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [services_schema](../modules/services_schema.md)

## Description

Machine-readable classification of one managed schema block.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `ABSENT` | `'absent'` | — |
| `LEGACY_EXPANDED_INLINE` | `'legacy-expanded-inline'` | — |
| `PROFILED` | `'profiled'` | — |
| `UNSUPPORTED_VERSION` | `'unsupported-version'` | — |
| `UNSUPPORTED_PROFILE` | `'unsupported-profile'` | — |
| `MALFORMED` | `'malformed'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ManagedSchemaBlockState (src/llm_wiki_cli/services/schema.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/commands/init_cmd.py"]
    n4["src/llm_wiki_cli/commands/status_cmd.py"]
    n5["src/llm_wiki_cli/commands/uninstall_cmd.py"]
    n6["src/llm_wiki_cli/commands/upgrade_cmd.py"]
    n7["src/llm_wiki_cli/services/rendering_lifecycle.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/services_schema.md"
    click n3 "../modules/init_cmd.md"
    click n4 "../modules/status_cmd.md"
    click n5 "../modules/uninstall_cmd.md"
    click n6 "../modules/upgrade_cmd.md"
    click n7 "../modules/rendering_lifecycle.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [services_schema](../modules/services_schema.md) | 0 | `ABSENT`, `LEGACY_EXPANDED_INLINE`, `MALFORMED`, `PROFILED`, `UNSUPPORTED_PROFILE`, `UNSUPPORTED_VERSION` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `init_cmd` | import | [init_cmd](../modules/init_cmd.md) |
| `status_cmd` | import | [status_cmd](../modules/status_cmd.md) |
| `uninstall_cmd` | import | [uninstall_cmd](../modules/uninstall_cmd.md) |
| `upgrade_cmd` | import | [upgrade_cmd](../modules/upgrade_cmd.md) |
| `rendering_lifecycle` | import | [rendering_lifecycle](../modules/rendering_lifecycle.md) |
