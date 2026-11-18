# SyncManifestError

**Location:** `src/llm_wiki_engine/sync_manifest.py:65`
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
    n0["SyncManifestError (src/llm_wiki_engine/sync_manifest.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/commands/team_cmd.py"]
    n3["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n4["src/llm_wiki_cli/services/ci_installer.py"]
    n5["src/llm_wiki_cli/services/documentation_query_builder.py"]
    n6["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n7["src/llm_wiki_cli/services/knowledge_generation.py"]
    n8["src/llm_wiki_cli/services/lint_service.py"]
    n9["src/llm_wiki_cli/services/team.py"]
    n10["src/llm_wiki_engine/knowledge_artifacts.py"]
    n11["src/llm_wiki_engine/knowledge_loader.py"]
    n12["src/llm_wiki_engine/source_retirement.py"]
    n13["_basis_from_payload (src/llm_wiki_engine/sync_manifest.py)"]
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
    click n0 "../modules/sync_manifest.md"
    click n2 "../modules/team_cmd.md"
    click n3 "../modules/bootstrap_runtime.md"
    click n4 "../modules/ci_installer.md"
    click n5 "../modules/documentation_query_builder.md"
    click n6 "../modules/documentation_wiki_input.md"
    click n7 "../modules/knowledge_generation.md"
    click n8 "../modules/lint_service.md"
    click n9 "../modules/team.md"
    click n10 "../modules/knowledge_artifacts.md"
    click n11 "../modules/knowledge_loader.md"
    click n12 "../modules/source_retirement.md"
    click n13 "../modules/sync_manifest.md"
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

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `team_cmd` | import | [team_cmd](../modules/team_cmd.md) | — |
| `bootstrap_runtime` | import | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `ci_installer` | import | [ci_installer](../modules/ci_installer.md) | — |
| `documentation_query_builder` | import | [documentation_query_builder](../modules/documentation_query_builder.md) | — |
| `documentation_wiki_input` | import | [documentation_wiki_input](../modules/documentation_wiki_input.md) | — |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
| `team` | import | [team](../modules/team.md) | — |
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `knowledge_loader` | import | [knowledge_loader](../modules/knowledge_loader.md) | — |
| `source_retirement` | import | [source_retirement](../modules/source_retirement.md) | — |
| `_basis_from_payload` | call | [sync_manifest](../modules/sync_manifest.md) | 1 |

> References: showing 12 of 36 logical references; 24 omitted by the 12-row generated summary limit.
