# TeamConfigError

**Location:** `src/llm_wiki_cli/services/team.py:65`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [team](../modules/team.md)

## Description

Raised when `.llm-wiki/team.json` is invalid.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["TeamConfigError (src/llm_wiki_cli/services/team.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/commands/generate_prompt_cmd.py"]
    n3["src/llm_wiki_cli/commands/trigger_cmd.py"]
    n4["_ensure_string_list (src/llm_wiki_cli/services/team.py)"]
    n5["_reject_unknown_keys (src/llm_wiki_cli/services/team.py)"]
    n6["load_team_config (src/llm_wiki_cli/services/team.py)"]
    n7["validate_team_config (src/llm_wiki_cli/services/team.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/team.md"
    click n2 "../modules/generate_prompt_cmd.md"
    click n3 "../modules/trigger_cmd.md"
    click n4 "../modules/team.md"
    click n5 "../modules/team.md"
    click n6 "../modules/team.md"
    click n7 "../modules/team.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [team](../modules/team.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `generate_prompt_cmd` | import | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) | — |
| `trigger_cmd` | import | [trigger_cmd](../modules/trigger_cmd.md) | — |
| `_ensure_string_list` | call | [team](../modules/team.md) | 1 |
| `_reject_unknown_keys` | call | [team](../modules/team.md) | 2 |
| `load_team_config` | call | [team](../modules/team.md) | 2 |
| `validate_team_config` | call | [team](../modules/team.md) | 10 |
