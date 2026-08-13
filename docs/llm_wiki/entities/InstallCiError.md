# InstallCiError

**Location:** `src/llm_wiki_cli/services/ci_installer.py:42`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [ci_installer](../modules/ci_installer.md)

## Description

Raised when a portable CI workflow cannot be installed safely.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InstallCiError (src/llm_wiki_cli/services/ci_installer.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/commands/install_ci_cmd.py"]
    n3["_project_directory (src/llm_wiki_cli/services/ci_installer.py)"]
    n4["_validate_default_selection_contract (src/llm_wiki_cli/services/ci_installer.py)"]
    n5["_validate_workflow_target (src/llm_wiki_cli/services/ci_installer.py)"]
    n6["_validated_project_path (src/llm_wiki_cli/services/ci_installer.py)"]
    n7["_without_github_expression (src/llm_wiki_cli/services/ci_installer.py)"]
    n8["install_ci_workflow (src/llm_wiki_cli/services/ci_installer.py)"]
    n9["normalize_action_ref (src/llm_wiki_cli/services/ci_installer.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/ci_installer.md"
    click n2 "../modules/install_ci_cmd.md"
    click n3 "../modules/ci_installer.md"
    click n4 "../modules/ci_installer.md"
    click n5 "../modules/ci_installer.md"
    click n6 "../modules/ci_installer.md"
    click n7 "../modules/ci_installer.md"
    click n8 "../modules/ci_installer.md"
    click n9 "../modules/ci_installer.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [ci_installer](../modules/ci_installer.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `install_ci_cmd` | import | [install_ci_cmd](../modules/install_ci_cmd.md) | — |
| `_project_directory` | call | [ci_installer](../modules/ci_installer.md) | 5 |
| `_validate_default_selection_contract` | call | [ci_installer](../modules/ci_installer.md) | 2 |
| `_validate_workflow_target` | call | [ci_installer](../modules/ci_installer.md) | 3 |
| `_validated_project_path` | call | [ci_installer](../modules/ci_installer.md) | 7 |
| `_without_github_expression` | call | [ci_installer](../modules/ci_installer.md) | 1 |
| `install_ci_workflow` | call | [ci_installer](../modules/ci_installer.md) | 6 |
| `normalize_action_ref` | call | [ci_installer](../modules/ci_installer.md) | 1 |
