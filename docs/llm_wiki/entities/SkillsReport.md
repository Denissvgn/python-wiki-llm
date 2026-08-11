# SkillsReport

**Location:** `src/llm_wiki_cli/services/skills.py:152`
**Kind:** Class
**Bases:** —
**Module:** [skills](../modules/skills.md)

**Decorators:** `@dataclass`

## Description

_Auto-generated from `SkillsReport` in `src/llm_wiki_cli/services/skills.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `ok` | `bool` | `True` | — |
| `dest_dir` | `str` | `''` | — |
| `skills` | `list[str]` | `field(default_factory=list)` | — |
| `operations` | `list[SkillOperation]` | `field(default_factory=list)` | — |
| `issues` | `list[dict[str, str]]` | `field(default_factory=list)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `to_dict` | `() -> dict[str, Any]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SkillsReport (src/llm_wiki_cli/services/skills.py)"]
    n1["_append_issue (src/llm_wiki_cli/services/skills.py)"]
    n2["_ensure_regular_directory (src/llm_wiki_cli/services/skills.py)"]
    n3["export_skills (src/llm_wiki_cli/services/skills.py)"]
    n4["install_reference_skill (src/llm_wiki_cli/services/skills.py)"]
    n5["install_skills (src/llm_wiki_cli/services/skills.py)"]
    n6["render_report_json (src/llm_wiki_cli/services/skills.py)"]
    n7["render_report_text (src/llm_wiki_cli/services/skills.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/skills.md"
    click n1 "../modules/skills.md"
    click n2 "../modules/skills.md"
    click n3 "../modules/skills.md"
    click n4 "../modules/skills.md"
    click n5 "../modules/skills.md"
    click n6 "../modules/skills.md"
    click n7 "../modules/skills.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [skills](../modules/skills.md) | 1 | `dest_dir`, `issues`, `ok`, `operations`, `skills` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_append_issue` | type_reference | [skills](../modules/skills.md) |
| `_ensure_regular_directory` | type_reference | [skills](../modules/skills.md) |
| `export_skills` | call | [skills](../modules/skills.md) |
| `export_skills` | type_reference | [skills](../modules/skills.md) |
| `install_reference_skill` | type_reference | [skills](../modules/skills.md) |
| `install_skills` | type_reference | [skills](../modules/skills.md) |
| `render_report_json` | type_reference | [skills](../modules/skills.md) |
| `render_report_text` | type_reference | [skills](../modules/skills.md) |
