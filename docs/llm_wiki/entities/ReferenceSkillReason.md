# ReferenceSkillReason

**Location:** `src/llm_wiki_cli/services/skills.py:116`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [skills](../modules/skills.md)

## Description

Stable lifecycle reason codes paired with :class:`ReferenceSkillState`.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `ABSENT` | `'managed-reference-absent'` | — |
| `CURRENT` | `'managed-reference-current'` | — |
| `LOCALLY_MODIFIED` | `'managed-reference-modified'` | — |
| `INCOMPLETE` | `'managed-reference-incomplete'` | — |
| `PACKAGE_MISSING` | `'managed-reference-package-missing'` | — |
| `INSTALL_ERROR` | `'managed-reference-install-failed'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ReferenceSkillReason (src/llm_wiki_cli/services/skills.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/commands/uninstall_cmd.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    click n0 "../modules/skills.md"
    click n3 "../modules/uninstall_cmd.md"
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

| Reference | Kind | Source |
|---|---|---|
| `uninstall_cmd` | import | [uninstall_cmd](../modules/uninstall_cmd.md) |
