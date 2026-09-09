# ValidatedKnowledgeArtifacts

**Location:** `src/llm_wiki_cli/services/knowledge_artifacts.py:113`
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
| `_validation` | `_ArtifactValidation \| None` | `field(default=None, init=False, repr=False, compare=False)` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ValidatedKnowledgeArtifacts (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n1["src/llm_wiki_cli/commands/knowledge_cmd.py"]
    n2["_validate_native_markdown_snapshot (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n3["_validate_native_marker (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n4["_validated_native_artifacts (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n5["_ArtifactValidation.__init__ (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n6["require_validated_artifacts (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n7["validate_knowledge_artifacts (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n8["validated_artifact_bytes (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n9["src/llm_wiki_cli/services/knowledge_freshness.py"]
    n10["src/llm_wiki_cli/services/knowledge_loader.py"]
    n11["_previous_committed_artifacts (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
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
    click n2 "../modules/documentation_wiki_input.md"
    click n3 "../modules/documentation_wiki_input.md"
    click n4 "../modules/documentation_wiki_input.md"
    click n5 "../modules/knowledge_artifacts.md"
    click n6 "../modules/knowledge_artifacts.md"
    click n7 "../modules/knowledge_artifacts.md"
    click n8 "../modules/knowledge_artifacts.md"
    click n9 "../modules/knowledge_freshness.md"
    click n10 "../modules/knowledge_loader.md"
    click n11 "../modules/knowledge_orchestration.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_artifacts](../modules/knowledge_artifacts.md) | 0 | `_validation`, `evaluated_envelope_hash`, `governance_hash`, `knowledge`, `knowledge_index_hash`, `surface_index_hash`, `surface_payload` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_cmd` | import | [knowledge_cmd](../modules/knowledge_cmd.md) | — |
| `_validate_native_markdown_snapshot` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) | — |
| `_validate_native_marker` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) | — |
| `_validated_native_artifacts` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) | — |
| `_ArtifactValidation.__init__` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `require_validated_artifacts` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `validate_knowledge_artifacts` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 1 |
| `validate_knowledge_artifacts` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `validated_artifact_bytes` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `knowledge_freshness` | import | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `knowledge_loader` | import | [knowledge_loader](../modules/knowledge_loader.md) | — |
| `_previous_committed_artifacts` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
