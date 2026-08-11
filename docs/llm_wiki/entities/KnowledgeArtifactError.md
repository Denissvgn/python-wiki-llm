# KnowledgeArtifactError

**Location:** `src/llm_wiki_cli/services/knowledge_artifacts.py:71`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_artifacts](../modules/knowledge_artifacts.md)

## Description

Field-specific failure while planning a generated artifact commit.

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
    n0["KnowledgeArtifactError (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/documentation_native.py"]
    n3["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n4["_decode_json_object (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n5["_nonnegative_integer (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n6["_reject_json_constant (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n7["_surface_page_index (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n8["_unique_json_object (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n9["_validate_asset_path_list (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n10["_validate_manifest_knowledge_parity (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n11["_validate_optional_surface_flow_fields (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n12["_validate_surface_asset_counts (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n13["_validate_surface_assets (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
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
    click n0 "../modules/knowledge_artifacts.md"
    click n2 "../modules/documentation_native.md"
    click n3 "../modules/documentation_wiki_input.md"
    click n4 "../modules/knowledge_artifacts.md"
    click n5 "../modules/knowledge_artifacts.md"
    click n6 "../modules/knowledge_artifacts.md"
    click n7 "../modules/knowledge_artifacts.md"
    click n8 "../modules/knowledge_artifacts.md"
    click n9 "../modules/knowledge_artifacts.md"
    click n10 "../modules/knowledge_artifacts.md"
    click n11 "../modules/knowledge_artifacts.md"
    click n12 "../modules/knowledge_artifacts.md"
    click n13 "../modules/knowledge_artifacts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_artifacts](../modules/knowledge_artifacts.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `documentation_native` | import | [documentation_native](../modules/documentation_native.md) | — |
| `documentation_wiki_input` | import | [documentation_wiki_input](../modules/documentation_wiki_input.md) | — |
| `_decode_json_object` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 4 |
| `_nonnegative_integer` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 1 |
| `_reject_json_constant` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 1 |
| `_surface_page_index` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 15 |
| `_unique_json_object` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 1 |
| `_validate_asset_path_list` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 3 |
| `_validate_manifest_knowledge_parity` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 16 |
| `_validate_optional_surface_flow_fields` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 1 |
| `_validate_surface_asset_counts` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 6 |
| `_validate_surface_assets` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 6 |

> References: showing 12 of 29 logical references; 17 omitted by the 12-row generated summary limit.
