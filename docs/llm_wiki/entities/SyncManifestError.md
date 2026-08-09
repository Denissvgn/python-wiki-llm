# SyncManifestError

**Location:** `src/llm_wiki_cli/services/sync_manifest.py:60`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [sync_manifest](../modules/sync_manifest.md)

## Description

Field-specific validation failure for decoded manifest state.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str, *, code: str \| None = None)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SyncManifestError (src/llm_wiki_cli/services/sync_manifest.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n3["src/llm_wiki_cli/services/ci_installer.py"]
    n4["src/llm_wiki_cli/services/documentation_query_builder.py"]
    n5["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n6["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n7["src/llm_wiki_cli/services/knowledge_generation.py"]
    n8["src/llm_wiki_cli/services/knowledge_loader.py"]
    n9["src/llm_wiki_cli/services/lint_service.py"]
    n10["_basis_from_payload (src/llm_wiki_cli/services/sync_manifest.py)"]
    n11["_captured_source_hashes (src/llm_wiki_cli/services/sync_manifest.py)"]
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
    click n0 "../modules/sync_manifest.md"
    click n2 "../modules/bootstrap_runtime.md"
    click n3 "../modules/ci_installer.md"
    click n4 "../modules/documentation_query_builder.md"
    click n5 "../modules/documentation_wiki_input.md"
    click n6 "../modules/knowledge_artifacts.md"
    click n7 "../modules/knowledge_generation.md"
    click n8 "../modules/knowledge_loader.md"
    click n9 "../modules/lint_service.md"
    click n10 "../modules/sync_manifest.md"
    click n11 "../modules/sync_manifest.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_manifest](../modules/sync_manifest.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `bootstrap_runtime` | import | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `ci_installer` | import | [ci_installer](../modules/ci_installer.md) |
| `documentation_query_builder` | import | [documentation_query_builder](../modules/documentation_query_builder.md) |
| `documentation_wiki_input` | import | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) |
| `knowledge_loader` | import | [knowledge_loader](../modules/knowledge_loader.md) |
| `lint_service` | import | [lint_service](../modules/lint_service.md) |
| `_basis_from_payload` | call | [sync_manifest](../modules/sync_manifest.md) |
| `_captured_source_hashes` | call | [sync_manifest](../modules/sync_manifest.md) |
| `_captured_source_hashes` | call | [sync_manifest](../modules/sync_manifest.md) |
| `_captured_source_hashes` | call | [sync_manifest](../modules/sync_manifest.md) |
