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
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/ci_installer.md"
    click n2 "../modules/install_ci_cmd.md"
    click n3 "../modules/ci_installer.md"
    click n4 "../modules/ci_installer.md"
    click n5 "../modules/ci_installer.md"
    click n6 "../modules/ci_installer.md"
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

| Reference | Kind | Source |
|---|---|---|
| `install_ci_cmd` | import | [install_ci_cmd](../modules/install_ci_cmd.md) |
| `_project_directory` | call | [ci_installer](../modules/ci_installer.md) |
| `_project_directory` | call | [ci_installer](../modules/ci_installer.md) |
| `_project_directory` | call | [ci_installer](../modules/ci_installer.md) |
| `_project_directory` | call | [ci_installer](../modules/ci_installer.md) |
| `_project_directory` | call | [ci_installer](../modules/ci_installer.md) |
| `_validate_default_selection_contract` | call | [ci_installer](../modules/ci_installer.md) |
| `_validate_default_selection_contract` | call | [ci_installer](../modules/ci_installer.md) |
| `_validate_workflow_target` | call | [ci_installer](../modules/ci_installer.md) |
| `_validate_workflow_target` | call | [ci_installer](../modules/ci_installer.md) |
| `_validate_workflow_target` | call | [ci_installer](../modules/ci_installer.md) |
| `_validated_project_path` | call | [ci_installer](../modules/ci_installer.md) |
