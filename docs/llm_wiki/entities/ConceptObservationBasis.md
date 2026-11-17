# ConceptObservationBasis

**Location:** `src/llm_wiki_engine/knowledge_evidence.py:90`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_evidence](../modules/knowledge_evidence.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One source-backed concept observation basis or explicit unknown result.

``unknown_reason`` is service-level diagnostic state and is not a v1 core
field. :meth:`to_evidence_payload` returns only fields accepted by the
persisted :class:`knowledge_model.EvidenceBasis` contract.

Optional normalization diagnostics describe only this fresh rejected observation.
They are excluded from equality and from the persisted evidence payload. A known
basis has no rejection detail; unknown evidence remains unknown regardless of how
precise the diagnostic is. Source completeness, structural hashing and stable
unknown reason codes retain their separate meanings.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `scope` | `str` | *required* | — |
| `source_path` | `str` | *required* | — |
| `extractor_ref` | `str` | *required* | — |
| `source_content_hash` | `str` | *required* | — |
| `concept_observation_hash` | `str \| None` | *required* | — |
| `unknown_reason` | `str \| None` | `None` | — |
| `normalization_diagnostic` | `NormalizationDiagnostic \| None` | `dataclass_field(default=None, repr=False, compare=False)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `is_known` | `() -> bool` | `@property` | Return whether this basis carries a reproducible observation hash. |
| `to_evidence_payload` | `() -> dict[str, str]` | — | Return the v1-compatible evidence-basis fields. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ConceptObservationBasis (src/llm_wiki_engine/knowledge_evidence.py)"]
    n1["current_infrastructure_bases (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n2["infrastructure_evidence_by_page (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n3["_live_basis_details (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n4["_build_evidence_baselines (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n5["_mark_untrusted_evidence (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n6["_preserve_unchanged_unknown_baselines (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n7["_validated_evidence_page_paths (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n8["_evidence_basis (src/llm_wiki_cli/services/knowledge_index.py)"]
    n9["_JoinedPage.basis (src/llm_wiki_cli/services/knowledge_index.py)"]
    n10["_runtime_live_concept_bases (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n11["_basis_from_payload (src/llm_wiki_cli/services/sync_manifest.py)"]
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
    click n0 "../modules/knowledge_evidence.md"
    click n1 "../modules/infrastructure_sync.md"
    click n2 "../modules/infrastructure_sync.md"
    click n3 "../modules/knowledge_freshness.md"
    click n4 "../modules/knowledge_generation.md"
    click n5 "../modules/knowledge_generation.md"
    click n6 "../modules/knowledge_generation.md"
    click n7 "../modules/knowledge_generation.md"
    click n8 "../modules/knowledge_index.md"
    click n9 "../modules/knowledge_index.md"
    click n10 "../modules/knowledge_orchestration.md"
    click n11 "../modules/sync_manifest.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_evidence](../modules/knowledge_evidence.md) | 3 | `concept_observation_hash`, `extractor_ref`, `normalization_diagnostic`, `scope`, `source_content_hash`, `source_path`, `unknown_reason` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `current_infrastructure_bases` | type_reference | [infrastructure_sync](../modules/infrastructure_sync.md) | — |
| `infrastructure_evidence_by_page` | type_reference | [infrastructure_sync](../modules/infrastructure_sync.md) | — |
| `_live_basis_details` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_build_evidence_baselines` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_mark_untrusted_evidence` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_preserve_unchanged_unknown_baselines` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_validated_evidence_page_paths` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_evidence_basis` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_JoinedPage.basis` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_runtime_live_concept_bases` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `_basis_from_payload` | call | [sync_manifest](../modules/sync_manifest.md) | 1 |
| `_basis_from_payload` | type_reference | [sync_manifest](../modules/sync_manifest.md) | — |

> References: showing 12 of 24 logical references; 12 omitted by the 12-row generated summary limit.
