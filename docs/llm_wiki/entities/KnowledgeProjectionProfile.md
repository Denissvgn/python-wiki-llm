# KnowledgeProjectionProfile

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:216`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

Out-of-band projection policies; never selected by artifact metadata.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `INTERNAL` | `'internal'` | — |
| `PUBLIC_PORTABLE` | `'public-portable'` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeProjectionProfile (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/cli_declarations.py"]
    n4["src/llm_wiki_cli/commands/site_cmd.py"]
    n5["_approved_public_repository_identity (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n6["_initial_omitted_counts (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n7["_project_bundle (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n8["_project_concept (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n9["_project_concept_kind (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n10["_project_endpoint (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n11["_project_relation (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n12["_project_relationship_kind (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n13["_project_relationships (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n14["_project_review (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n0 --> n1
    n0 --> n2
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
    n14 --> n0
    click n0 "../modules/knowledge_model.md"
    click n3 "../modules/cli_declarations.md"
    click n4 "../modules/site_cmd.md"
    click n5 "../modules/knowledge_projection.md"
    click n6 "../modules/knowledge_projection.md"
    click n7 "../modules/knowledge_projection.md"
    click n8 "../modules/knowledge_projection.md"
    click n9 "../modules/knowledge_projection.md"
    click n10 "../modules/knowledge_projection.md"
    click n11 "../modules/knowledge_projection.md"
    click n12 "../modules/knowledge_projection.md"
    click n13 "../modules/knowledge_projection.md"
    click n14 "../modules/knowledge_projection.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `INTERNAL`, `PUBLIC_PORTABLE` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `cli_declarations` | import | [cli_declarations](../modules/cli_declarations.md) | — |
| `site_cmd` | import | [site_cmd](../modules/site_cmd.md) | — |
| `_approved_public_repository_identity` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_initial_omitted_counts` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_bundle` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_concept` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_concept_kind` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_endpoint` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_relation` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_relationship_kind` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_relationships` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_review` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |

> References: showing 12 of 24 logical references; 12 omitted by the 12-row generated summary limit.
