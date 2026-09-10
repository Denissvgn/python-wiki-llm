# TeamConfigError

**Location:** `src/llm_wiki_cli/services/team.py:71`
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
    n3["_run_check (src/llm_wiki_cli/commands/team_cmd.py)"]
    n4["src/llm_wiki_cli/commands/trigger_cmd.py"]
    n5["src/llm_wiki_cli/services/lint_service.py"]
    n6["_ensure_string_list (src/llm_wiki_cli/services/team.py)"]
    n7["_reject_unknown_keys (src/llm_wiki_cli/services/team.py)"]
    n8["_required_path_states (src/llm_wiki_cli/services/team.py)"]
    n9["_resolve_required_path (src/llm_wiki_cli/services/team.py)"]
    n10["_validate_required_relative_path (src/llm_wiki_cli/services/team.py)"]
    n11["build_team_issues (src/llm_wiki_cli/services/team.py)"]
    n12["load_team_config (src/llm_wiki_cli/services/team.py)"]
    n13["resolve_team_policy (src/llm_wiki_cli/services/team.py)"]
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
    n12 --> n0
    n13 --> n0
    click n0 "../modules/team.md"
    click n2 "../modules/generate_prompt_cmd.md"
    click n3 "../modules/team_cmd.md"
    click n4 "../modules/trigger_cmd.md"
    click n5 "../modules/lint_service.md"
    click n6 "../modules/team.md"
    click n7 "../modules/team.md"
    click n8 "../modules/team.md"
    click n9 "../modules/team.md"
    click n10 "../modules/team.md"
    click n11 "../modules/team.md"
    click n12 "../modules/team.md"
    click n13 "../modules/team.md"
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
| `_run_check` | call | [team_cmd](../modules/team_cmd.md) | 1 |
| `trigger_cmd` | import | [trigger_cmd](../modules/trigger_cmd.md) | — |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
| `_ensure_string_list` | call | [team](../modules/team.md) | 1 |
| `_reject_unknown_keys` | call | [team](../modules/team.md) | 2 |
| `_required_path_states` | call | [team](../modules/team.md) | 1 |
| `_resolve_required_path` | call | [team](../modules/team.md) | 2 |
| `_validate_required_relative_path` | call | [team](../modules/team.md) | 1 |
| `build_team_issues` | call | [team](../modules/team.md) | 1 |
| `load_team_config` | call | [team](../modules/team.md) | 3 |
| `resolve_team_policy` | call | [team](../modules/team.md) | 3 |

> References: showing 12 of 14 logical references; 2 omitted by the 12-row generated summary limit.
