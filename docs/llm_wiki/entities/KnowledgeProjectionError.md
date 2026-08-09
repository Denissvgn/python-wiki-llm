# KnowledgeProjectionError

**Location:** `src/llm_wiki_cli/services/knowledge_projection.py:196`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_projection](../modules/knowledge_projection.md)

## Description

Stable failure at the validated projection boundary.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(code: str, field: str, message: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeProjectionError (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/commands/obsidian_cmd.py"]
    n3["_approved_public_repository_identity (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n4["_project_freshness (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n5["_projection_concept_summary_unchecked (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n6["_projection_profile (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n7["_relationship_limit (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n8["_require_bool (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n9["_require_enum (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n10["_require_exact_fields (src/llm_wiki_cli/services/knowledge_projection.py)"]
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
    click n0 "../modules/knowledge_projection.md"
    click n2 "../modules/obsidian_cmd.md"
    click n3 "../modules/knowledge_projection.md"
    click n4 "../modules/knowledge_projection.md"
    click n5 "../modules/knowledge_projection.md"
    click n6 "../modules/knowledge_projection.md"
    click n7 "../modules/knowledge_projection.md"
    click n8 "../modules/knowledge_projection.md"
    click n9 "../modules/knowledge_projection.md"
    click n10 "../modules/knowledge_projection.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_projection](../modules/knowledge_projection.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `obsidian_cmd` | import | [obsidian_cmd](../modules/obsidian_cmd.md) |
| `_approved_public_repository_identity` | call | [knowledge_projection](../modules/knowledge_projection.md) |
| `_approved_public_repository_identity` | call | [knowledge_projection](../modules/knowledge_projection.md) |
| `_approved_public_repository_identity` | call | [knowledge_projection](../modules/knowledge_projection.md) |
| `_project_freshness` | call | [knowledge_projection](../modules/knowledge_projection.md) |
| `_project_freshness` | call | [knowledge_projection](../modules/knowledge_projection.md) |
| `_projection_concept_summary_unchecked` | call | [knowledge_projection](../modules/knowledge_projection.md) |
| `_projection_profile` | call | [knowledge_projection](../modules/knowledge_projection.md) |
| `_relationship_limit` | call | [knowledge_projection](../modules/knowledge_projection.md) |
| `_require_bool` | call | [knowledge_projection](../modules/knowledge_projection.md) |
| `_require_enum` | call | [knowledge_projection](../modules/knowledge_projection.md) |
| `_require_exact_fields` | call | [knowledge_projection](../modules/knowledge_projection.md) |
