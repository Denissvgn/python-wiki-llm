# KnowledgeProjection

**Location:** `src/llm_wiki_cli/services/knowledge_projection.py:207`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_projection](../modules/knowledge_projection.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One deterministic exporter-facing projection.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `schema_version` | `str` | *required* | — |
| `profile` | `KnowledgeProjectionProfile` | *required* | — |
| `source_knowledge_hash` | `str` | *required* | — |
| `bundle` | `Mapping[str, Any]` | *required* | — |
| `concepts` | `Mapping[str, Mapping[str, Any]]` | *required* | — |
| `warnings` | `tuple[str, ...]` | *required* | — |
| `omitted_fields` | `Mapping[str, int]` | *required* | — |
| `freshness` | `str \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | Detach and recursively freeze every caller-supplied container. |
| `to_payload` | `() -> dict[str, Any]` | — | Return a detached JSON-compatible payload. |
| `concept_for_path` | `(canonical_path: str) -> Mapping[str, Any] \| None` | — | Return one projected concept by exact canonical Markdown path. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeProjection (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n1["_knowledge_projection (src/llm_wiki_cli/commands/obsidian_cmd.py)"]
    n2["_load_hub_knowledge_projections (src/llm_wiki_cli/commands/site_cmd.py)"]
    n3["_load_knowledge_projection (src/llm_wiki_cli/commands/site_cmd.py)"]
    n4["_approved_public_repository_identity (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n5["_initial_omitted_counts (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n6["_project_bundle (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n7["_project_concept (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n8["_project_concept_kind (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n9["_project_endpoint (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n10["_project_relation (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n11["_project_relationship_kind (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n12["_project_relationships (src/llm_wiki_cli/services/knowledge_projection.py)"]
    n1 --> n0
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
    click n0 "../modules/knowledge_projection.md"
    click n1 "../modules/obsidian_cmd.md"
    click n2 "../modules/site_cmd.md"
    click n3 "../modules/site_cmd.md"
    click n4 "../modules/knowledge_projection.md"
    click n5 "../modules/knowledge_projection.md"
    click n6 "../modules/knowledge_projection.md"
    click n7 "../modules/knowledge_projection.md"
    click n8 "../modules/knowledge_projection.md"
    click n9 "../modules/knowledge_projection.md"
    click n10 "../modules/knowledge_projection.md"
    click n11 "../modules/knowledge_projection.md"
    click n12 "../modules/knowledge_projection.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_projection](../modules/knowledge_projection.md) | 3 | `bundle`, `concepts`, `freshness`, `omitted_fields`, `profile`, `schema_version`, `source_knowledge_hash`, `warnings` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_knowledge_projection` | type_reference | [obsidian_cmd](../modules/obsidian_cmd.md) | — |
| `_load_hub_knowledge_projections` | type_reference | [site_cmd](../modules/site_cmd.md) | — |
| `_load_knowledge_projection` | type_reference | [site_cmd](../modules/site_cmd.md) | — |
| `_approved_public_repository_identity` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_initial_omitted_counts` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_bundle` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_concept` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_concept_kind` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_endpoint` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_relation` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_relationship_kind` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `_project_relationships` | type_reference | [knowledge_projection](../modules/knowledge_projection.md) | — |

> References: showing 12 of 49 logical references; 37 omitted by the 12-row generated summary limit.
