# ConceptKind

**Location:** `src/llm_wiki_engine/knowledge_model.py:120`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

Versioned domain taxonomy independent of the current page layout.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `SOURCE_MODULE` | `'source-module'` | — |
| `CODE_ENTITY` | `'code-entity'` | — |
| `WORKFLOW` | `'workflow'` | — |
| `GUIDE` | `'guide'` | — |
| `USER_FLOW` | `'user-flow'` | — |
| `INFRASTRUCTURE_RESOURCE` | `'infrastructure-resource'` | — |
| `API_CONTRACT` | `'api-contract'` | — |
| `DEPENDENCY_VIEW` | `'dependency-view'` | — |
| `NAVIGATION_DOCUMENT` | `'navigation-document'` | — |
| `CHANGE_LOG_DOCUMENT` | `'change-log-document'` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `is_document_only` | `() -> bool` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ConceptKind (src/llm_wiki_engine/knowledge_model.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/context_packet.py"]
    n4["src/llm_wiki_cli/services/knowledge_projection.py"]
    n5["src/llm_wiki_engine/knowledge_artifacts.py"]
    n6["src/llm_wiki_engine/knowledge_coverage.py"]
    n7["src/llm_wiki_engine/knowledge_governance.py"]
    n8["_structural_facet (src/llm_wiki_engine/knowledge_index.py)"]
    n9["_builtin_concept_specs (src/llm_wiki_engine/knowledge_kinds.py)"]
    n10["KindRegistry._check_concept (src/llm_wiki_engine/knowledge_kinds.py)"]
    n11["KindRegistry.with_concept_kind (src/llm_wiki_engine/knowledge_kinds.py)"]
    n12["concept_kind_for_page_kind (src/llm_wiki_engine/knowledge_model.py)"]
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
    click n0 "../modules/knowledge_model.md"
    click n3 "../modules/context_packet.md"
    click n4 "../modules/knowledge_projection.md"
    click n5 "../modules/knowledge_artifacts.md"
    click n6 "../modules/knowledge_coverage.md"
    click n7 "../modules/knowledge_governance.md"
    click n8 "../modules/knowledge_index.md"
    click n9 "../modules/knowledge_kinds.md"
    click n10 "../modules/knowledge_kinds.md"
    click n11 "../modules/knowledge_kinds.md"
    click n12 "../modules/knowledge_model.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 1 | `API_CONTRACT`, `CHANGE_LOG_DOCUMENT`, `CODE_ENTITY`, `DEPENDENCY_VIEW`, `GUIDE`, `INFRASTRUCTURE_RESOURCE`, `NAVIGATION_DOCUMENT`, `SOURCE_MODULE`, `USER_FLOW`, `WORKFLOW` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `context_packet` | import | [context_packet](../modules/context_packet.md) | — |
| `knowledge_projection` | import | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `knowledge_coverage` | import | [knowledge_coverage](../modules/knowledge_coverage.md) | — |
| `knowledge_governance` | import | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `_structural_facet` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_builtin_concept_specs` | type_reference | [knowledge_kinds](../modules/knowledge_kinds.md) | — |
| `KindRegistry._check_concept` | type_reference | [knowledge_kinds](../modules/knowledge_kinds.md) | — |
| `KindRegistry.with_concept_kind` | type_reference | [knowledge_kinds](../modules/knowledge_kinds.md) | — |
| `concept_kind_for_page_kind` | type_reference | [knowledge_model](../modules/knowledge_model.md) | — |
