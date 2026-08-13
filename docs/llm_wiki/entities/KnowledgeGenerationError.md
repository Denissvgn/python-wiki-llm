# KnowledgeGenerationError

**Location:** `src/llm_wiki_cli/services/knowledge_generation.py:85`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_generation](../modules/knowledge_generation.md)

## Description

Field-specific failure at the shared generation-planning boundary.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeGenerationError (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n1["ValueError"]
    n2["_application_knowledge_extensions (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n3["_build_knowledge_generation_plan (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n4["_exact_source_mapping (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n5["_next_manifest_mapping (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n6["_raise_page_map_parity (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n7["_structural_page_paths (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n8["_surface_index_bytes (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n9["_validated_consumed_inputs (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n10["_validated_evidence_page_paths (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n11["_validated_inventory (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n12["_validated_page_maps (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n13["_validated_previous_producer (src/llm_wiki_cli/services/knowledge_generation.py)"]
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
    click n0 "../modules/knowledge_generation.md"
    click n2 "../modules/knowledge_generation.md"
    click n3 "../modules/knowledge_generation.md"
    click n4 "../modules/knowledge_generation.md"
    click n5 "../modules/knowledge_generation.md"
    click n6 "../modules/knowledge_generation.md"
    click n7 "../modules/knowledge_generation.md"
    click n8 "../modules/knowledge_generation.md"
    click n9 "../modules/knowledge_generation.md"
    click n10 "../modules/knowledge_generation.md"
    click n11 "../modules/knowledge_generation.md"
    click n12 "../modules/knowledge_generation.md"
    click n13 "../modules/knowledge_generation.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_generation](../modules/knowledge_generation.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_application_knowledge_extensions` | call | [knowledge_generation](../modules/knowledge_generation.md) | 2 |
| `_build_knowledge_generation_plan` | call | [knowledge_generation](../modules/knowledge_generation.md) | 4 |
| `_exact_source_mapping` | call | [knowledge_generation](../modules/knowledge_generation.md) | 3 |
| `_next_manifest_mapping` | call | [knowledge_generation](../modules/knowledge_generation.md) | 1 |
| `_raise_page_map_parity` | call | [knowledge_generation](../modules/knowledge_generation.md) | 2 |
| `_structural_page_paths` | call | [knowledge_generation](../modules/knowledge_generation.md) | 2 |
| `_surface_index_bytes` | call | [knowledge_generation](../modules/knowledge_generation.md) | 4 |
| `_validated_consumed_inputs` | call | [knowledge_generation](../modules/knowledge_generation.md) | 5 |
| `_validated_evidence_page_paths` | call | [knowledge_generation](../modules/knowledge_generation.md) | 2 |
| `_validated_inventory` | call | [knowledge_generation](../modules/knowledge_generation.md) | 6 |
| `_validated_page_maps` | call | [knowledge_generation](../modules/knowledge_generation.md) | 6 |
| `_validated_previous_producer` | call | [knowledge_generation](../modules/knowledge_generation.md) | 1 |

> References: showing 12 of 20 logical references; 8 omitted by the 12-row generated summary limit.
