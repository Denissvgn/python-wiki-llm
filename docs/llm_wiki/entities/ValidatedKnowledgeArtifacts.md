# ValidatedKnowledgeArtifacts

**Location:** `src/llm_wiki_cli/services/knowledge_artifacts.py:130`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_artifacts](../modules/knowledge_artifacts.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Validated canonical projections and their exact-byte commitments.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `surface_payload` | `Mapping[str, Any]` | *required* | — |
| `knowledge` | `KnowledgeIndex` | *required* | — |
| `surface_index_hash` | `str` | *required* | — |
| `knowledge_index_hash` | `str` | *required* | — |
| `evaluated_envelope_hash` | `str` | *required* | — |
| `governance_hash` | `str \| None` | `None` | — |
| `storage_objects` | `Mapping[str, bytes]` | `field(default_factory=dict, repr=False)` | — |
| `storage_statistics` | `Mapping[str, Any]` | `field(default_factory=dict, repr=False)` | — |
| `knowledge_payload` | `Mapping[str, Any]` | `field(default_factory=dict, repr=False, compare=False)` | — |
| `_validation` | `_ArtifactValidation \| None` | `field(default=None, init=False, repr=False, compare=False)` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ValidatedKnowledgeArtifacts (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n1["src/llm_wiki_cli/commands/knowledge_cmd.py"]
    n2["DocumentationGraphQueryService._build_typed_graph_indexes (src/llm_wiki_cli/services/documentation_queries.py)"]
    n3["_validate_native_markdown_snapshot (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n4["_validate_native_marker (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n5["_validated_native_artifacts (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n6["_ArtifactValidation.__init__ (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n7["build_knowledge_commit_plan (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n8["require_validated_artifacts (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n9["validate_knowledge_artifacts (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n10["validated_artifact_bytes (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n11["src/llm_wiki_cli/services/knowledge_consumption.py"]
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
    click n0 "../modules/knowledge_artifacts.md"
    click n1 "../modules/knowledge_cmd.md"
    click n2 "../modules/documentation_queries.md"
    click n3 "../modules/documentation_wiki_input.md"
    click n4 "../modules/documentation_wiki_input.md"
    click n5 "../modules/documentation_wiki_input.md"
    click n6 "../modules/knowledge_artifacts.md"
    click n7 "../modules/knowledge_artifacts.md"
    click n8 "../modules/knowledge_artifacts.md"
    click n9 "../modules/knowledge_artifacts.md"
    click n10 "../modules/knowledge_artifacts.md"
    click n11 "../modules/knowledge_consumption.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_artifacts](../modules/knowledge_artifacts.md) | 0 | `_validation`, `evaluated_envelope_hash`, `governance_hash`, `knowledge`, `knowledge_index_hash`, `knowledge_payload`, `storage_objects`, `storage_statistics`, `surface_index_hash`, `surface_payload` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_cmd` | import | [knowledge_cmd](../modules/knowledge_cmd.md) | — |
| `DocumentationGraphQueryService._build_typed_graph_indexes` | type_reference | [documentation_queries](../modules/documentation_queries.md) | — |
| `_validate_native_markdown_snapshot` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) | — |
| `_validate_native_marker` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) | — |
| `_validated_native_artifacts` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) | — |
| `_ArtifactValidation.__init__` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `build_knowledge_commit_plan` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `require_validated_artifacts` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `validate_knowledge_artifacts` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 1 |
| `validate_knowledge_artifacts` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `validated_artifact_bytes` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `knowledge_consumption` | import | [knowledge_consumption](../modules/knowledge_consumption.md) | — |

> References: showing 12 of 16 logical references; 4 omitted by the 12-row generated summary limit.
