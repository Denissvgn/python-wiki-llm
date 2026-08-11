# WindowsIdentityUnavailableError

**Location:** `src/llm_wiki_cli/services/filesystem_guard.py:64`
**Kind:** Class
**Bases:** `OSError`
**Module:** [filesystem_guard](../modules/filesystem_guard.md)

## Description

Raised when Windows cannot expose a stable filesystem object identity.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WindowsIdentityUnavailableError (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n1["OSError"]
    n2["src/llm_wiki_cli/services/documentation_policy.py"]
    n3["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n4["windows_object_identity_from_values (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n5["WindowsObjectIdentity.__post_init__ (src/llm_wiki_cli/services/filesystem_guard.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/filesystem_guard.md"
    click n2 "../modules/documentation_policy.md"
    click n3 "../modules/documentation_wiki_input.md"
    click n4 "../modules/filesystem_guard.md"
    click n5 "../modules/filesystem_guard.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [filesystem_guard](../modules/filesystem_guard.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `OSError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `documentation_policy` | import | [documentation_policy](../modules/documentation_policy.md) |
| `documentation_wiki_input` | import | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `windows_object_identity_from_values` | call | [filesystem_guard](../modules/filesystem_guard.md) |
| `WindowsObjectIdentity.__post_init__` | call | [filesystem_guard](../modules/filesystem_guard.md) |
