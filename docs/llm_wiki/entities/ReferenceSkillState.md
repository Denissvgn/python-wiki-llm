# ReferenceSkillState

**Location:** `src/llm_wiki_cli/services/skills.py:116`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [skills](../modules/skills.md)

## Description

Stable live/provisioning states for the managed reference skill.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `ABSENT` | `'absent'` | — |
| `CURRENT` | `'current'` | — |
| `LOCALLY_MODIFIED` | `'locally_modified'` | — |
| `INCOMPLETE` | `'incomplete'` | — |
| `PACKAGE_MISSING` | `'package_missing'` | — |
| `INSTALL_ERROR` | `'install_error'` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ReferenceSkillState (src/llm_wiki_cli/services/skills.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/commands/init_cmd.py"]
    n4["src/llm_wiki_cli/commands/status_cmd.py"]
    n5["src/llm_wiki_cli/commands/uninstall_cmd.py"]
    n6["select_render_profile (src/llm_wiki_cli/services/rendering_lifecycle.py)"]
    n7["_reference_verification (src/llm_wiki_cli/services/skills.py)"]
    n8["src/llm_wiki_cli/services/upgrade_runtime.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/skills.md"
    click n3 "../modules/init_cmd.md"
    click n4 "../modules/status_cmd.md"
    click n5 "../modules/uninstall_cmd.md"
    click n6 "../modules/rendering_lifecycle.md"
    click n7 "../modules/skills.md"
    click n8 "../modules/upgrade_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [skills](../modules/skills.md) | 0 | `ABSENT`, `CURRENT`, `INCOMPLETE`, `INSTALL_ERROR`, `LOCALLY_MODIFIED`, `PACKAGE_MISSING` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `init_cmd` | import | [init_cmd](../modules/init_cmd.md) | — |
| `status_cmd` | import | [status_cmd](../modules/status_cmd.md) | — |
| `uninstall_cmd` | import | [uninstall_cmd](../modules/uninstall_cmd.md) | — |
| `select_render_profile` | type_reference | [rendering_lifecycle](../modules/rendering_lifecycle.md) | — |
| `_reference_verification` | type_reference | [skills](../modules/skills.md) | — |
| `upgrade_runtime` | import | [upgrade_runtime](../modules/upgrade_runtime.md) | — |
