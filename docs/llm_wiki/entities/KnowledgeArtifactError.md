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
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/knowledge_artifacts.md"
    click n2 "../modules/documentation_native.md"
    click n3 "../modules/documentation_wiki_input.md"
    click n4 "../modules/knowledge_artifacts.md"
    click n5 "../modules/knowledge_artifacts.md"
    click n6 "../modules/knowledge_artifacts.md"
    click n7 "../modules/knowledge_artifacts.md"
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

| Reference | Kind | Source |
|---|---|---|
| `documentation_native` | import | [documentation_native](../modules/documentation_native.md) |
| `documentation_wiki_input` | import | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_decode_json_object` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `_decode_json_object` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `_decode_json_object` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `_decode_json_object` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `_nonnegative_integer` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `_reject_json_constant` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `_surface_page_index` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `_surface_page_index` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `_surface_page_index` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `_surface_page_index` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
