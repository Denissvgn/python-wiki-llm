# SkillsError

**Location:** `src/llm_wiki_cli/services/skills.py:101`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [skills](../modules/skills.md)

## Description

Raised for invalid skill list/export/install requests.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SkillsError (src/llm_wiki_cli/services/skills.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/commands/skills_cmd.py"]
    n3["_ensure_safe_base (src/llm_wiki_cli/services/skills.py)"]
    n4["_preflight_reference_requirement (src/llm_wiki_cli/services/skills.py)"]
    n5["_select_skills (src/llm_wiki_cli/services/skills.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/skills.md"
    click n2 "../modules/skills_cmd.md"
    click n3 "../modules/skills.md"
    click n4 "../modules/skills.md"
    click n5 "../modules/skills.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [skills](../modules/skills.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `skills_cmd` | import | [skills_cmd](../modules/skills_cmd.md) |
| `_ensure_safe_base` | call | [skills](../modules/skills.md) |
| `_preflight_reference_requirement` | call | [skills](../modules/skills.md) |
| `_preflight_reference_requirement` | call | [skills](../modules/skills.md) |
| `_preflight_reference_requirement` | call | [skills](../modules/skills.md) |
| `_select_skills` | call | [skills](../modules/skills.md) |
| `_select_skills` | call | [skills](../modules/skills.md) |
