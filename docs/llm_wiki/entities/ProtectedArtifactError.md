# ProtectedArtifactError

**Location:** `src/llm_wiki_cli/services/protected_artifacts.py:75`
**Kind:** Class
**Bases:** `RuntimeError`
**Module:** [protected_artifacts](../modules/protected_artifacts.md)

## Description

Base error for protected artifact storage.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ProtectedArtifactError (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n1["RuntimeError"]
    n2["ProtectedArtifactDurabilityError (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n3["ProtectedArtifactIntegrityError (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n4["ProtectedArtifactLimitError (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n5["ProtectedArtifactLockError (src/llm_wiki_cli/services/protected_artifacts.py)"]
    n6["src/llm_wiki_cli/services/calibration/controller.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/protected_artifacts.md"
    click n2 "../modules/protected_artifacts.md"
    click n3 "../modules/protected_artifacts.md"
    click n4 "../modules/protected_artifacts.md"
    click n5 "../modules/protected_artifacts.md"
    click n6 "../modules/controller.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [protected_artifacts](../modules/protected_artifacts.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `RuntimeError` | — |
| Subclass | `ProtectedArtifactDurabilityError` | [protected_artifacts](../modules/protected_artifacts.md) |
| Subclass | `ProtectedArtifactIntegrityError` | [protected_artifacts](../modules/protected_artifacts.md) |
| Subclass | `ProtectedArtifactLimitError` | [protected_artifacts](../modules/protected_artifacts.md) |
| Subclass | `ProtectedArtifactLockError` | [protected_artifacts](../modules/protected_artifacts.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `controller` | import | [controller](../modules/controller.md) |
