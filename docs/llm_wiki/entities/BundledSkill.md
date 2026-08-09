# BundledSkill

**Location:** `src/llm_wiki_cli/services/skills.py:63`
**Kind:** Class
**Bases:** —
**Module:** [skills](../modules/skills.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `BundledSkill` in `src/llm_wiki_cli/services/skills.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `skill_id` | `str` | *required* | — |
| `name` | `str` | *required* | — |
| `description` | `str` | *required* | — |
| `path` | `Path` | *required* | — |
| `files` | `tuple[str, ...]` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `to_dict` | `() -> dict[str, Any]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["BundledSkill (src/llm_wiki_cli/services/skills.py)"]
    n1["_select_skills (src/llm_wiki_cli/services/skills.py)"]
    n2["list_bundled_skills (src/llm_wiki_cli/services/skills.py)"]
    n3["render_skill_list_json (src/llm_wiki_cli/services/skills.py)"]
    n4["render_skill_list_text (src/llm_wiki_cli/services/skills.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/skills.md"
    click n1 "../modules/skills.md"
    click n2 "../modules/skills.md"
    click n3 "../modules/skills.md"
    click n4 "../modules/skills.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [skills](../modules/skills.md) | 1 | `description`, `files`, `name`, `path`, `skill_id` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_select_skills` | type_reference | [skills](../modules/skills.md) |
| `list_bundled_skills` | call | [skills](../modules/skills.md) |
| `list_bundled_skills` | type_reference | [skills](../modules/skills.md) |
| `render_skill_list_json` | type_reference | [skills](../modules/skills.md) |
| `render_skill_list_text` | type_reference | [skills](../modules/skills.md) |
