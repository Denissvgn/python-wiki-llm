# KnowledgeIndexBuildError

**Location:** `src/llm_wiki_cli/services/knowledge_index.py:129`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_index](../modules/knowledge_index.md)

## Description

Field-specific failure at the pure knowledge-index join boundary.

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
    n0["KnowledgeIndexBuildError (src/llm_wiki_cli/services/knowledge_index.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/knowledge_generation.py"]
    n3["_expected_page_coordinates (src/llm_wiki_cli/services/knowledge_index.py)"]
    n4["_nonempty_string (src/llm_wiki_cli/services/knowledge_index.py)"]
    n5["_reject_extra_state (src/llm_wiki_cli/services/knowledge_index.py)"]
    n6["_relative_path (src/llm_wiki_cli/services/knowledge_index.py)"]
    n7["_require_exact_keys (src/llm_wiki_cli/services/knowledge_index.py)"]
    n8["_surface_pages (src/llm_wiki_cli/services/knowledge_index.py)"]
    n9["_typed_mapping (src/llm_wiki_cli/services/knowledge_index.py)"]
    n10["_validate_and_join_inputs (src/llm_wiki_cli/services/knowledge_index.py)"]
    n11["_validate_observation_endpoint (src/llm_wiki_cli/services/knowledge_index.py)"]
    n12["_validate_observation_source_syntax (src/llm_wiki_cli/services/knowledge_index.py)"]
    n13["_validate_page_evidence (src/llm_wiki_cli/services/knowledge_index.py)"]
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
    click n0 "../modules/knowledge_index.md"
    click n2 "../modules/knowledge_generation.md"
    click n3 "../modules/knowledge_index.md"
    click n4 "../modules/knowledge_index.md"
    click n5 "../modules/knowledge_index.md"
    click n6 "../modules/knowledge_index.md"
    click n7 "../modules/knowledge_index.md"
    click n8 "../modules/knowledge_index.md"
    click n9 "../modules/knowledge_index.md"
    click n10 "../modules/knowledge_index.md"
    click n11 "../modules/knowledge_index.md"
    click n12 "../modules/knowledge_index.md"
    click n13 "../modules/knowledge_index.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_index](../modules/knowledge_index.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_expected_page_coordinates` | call | [knowledge_index](../modules/knowledge_index.md) | 2 |
| `_nonempty_string` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
| `_reject_extra_state` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
| `_relative_path` | call | [knowledge_index](../modules/knowledge_index.md) | 5 |
| `_require_exact_keys` | call | [knowledge_index](../modules/knowledge_index.md) | 3 |
| `_surface_pages` | call | [knowledge_index](../modules/knowledge_index.md) | 10 |
| `_typed_mapping` | call | [knowledge_index](../modules/knowledge_index.md) | 3 |
| `_validate_and_join_inputs` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
| `_validate_observation_endpoint` | call | [knowledge_index](../modules/knowledge_index.md) | 12 |
| `_validate_observation_source_syntax` | call | [knowledge_index](../modules/knowledge_index.md) | 2 |
| `_validate_page_evidence` | call | [knowledge_index](../modules/knowledge_index.md) | 16 |

> References: showing 12 of 20 logical references; 8 omitted by the 12-row generated summary limit.
