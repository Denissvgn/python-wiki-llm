# UnsafeUninstallPathError

**Location:** `src/llm_wiki_cli/commands/uninstall_cmd.py:58`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [uninstall_cmd](../modules/uninstall_cmd.md)

## Description

Raised when an uninstall-owned path could escape the project tree.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["UnsafeUninstallPathError (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n1["ValueError"]
    n2["_preflight_hooks (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n3["_remove_ci_workflow (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n4["_remove_hooks (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n5["_remove_reference_skill (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n6["_remove_runtime_artifacts (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n7["_remove_wiki_dir (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n8["_require_safe_hook_path (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n9["_validate_hook_plan (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n10["_validate_reference_plan (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n11["_validate_runtime_plan (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n12["run (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
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
    click n0 "../modules/uninstall_cmd.md"
    click n2 "../modules/uninstall_cmd.md"
    click n3 "../modules/uninstall_cmd.md"
    click n4 "../modules/uninstall_cmd.md"
    click n5 "../modules/uninstall_cmd.md"
    click n6 "../modules/uninstall_cmd.md"
    click n7 "../modules/uninstall_cmd.md"
    click n8 "../modules/uninstall_cmd.md"
    click n9 "../modules/uninstall_cmd.md"
    click n10 "../modules/uninstall_cmd.md"
    click n11 "../modules/uninstall_cmd.md"
    click n12 "../modules/uninstall_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [uninstall_cmd](../modules/uninstall_cmd.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_preflight_hooks` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 3 |
| `_remove_ci_workflow` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 1 |
| `_remove_hooks` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 1 |
| `_remove_reference_skill` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 2 |
| `_remove_runtime_artifacts` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 2 |
| `_remove_wiki_dir` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 3 |
| `_require_safe_hook_path` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 1 |
| `_validate_hook_plan` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 1 |
| `_validate_reference_plan` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 1 |
| `_validate_runtime_plan` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 1 |
| `run` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 2 |
