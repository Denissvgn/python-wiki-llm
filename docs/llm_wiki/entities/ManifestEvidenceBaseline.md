# ManifestEvidenceBaseline

**Location:** `src/llm_wiki_cli/services/sync_manifest.py:252`
**Kind:** Class
**Bases:** —
**Module:** [sync_manifest](../modules/sync_manifest.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Known or explicitly unknown evidence for one active concept page.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `basis` | `ConceptObservationBasis \| None` | `None` | — |
| `unknown_reason` | `str \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `is_known` | `() -> bool` | `@property` | — |
| `from_basis` | `(basis: ConceptObservationBasis) -> ManifestEvidenceBaseline` | `@classmethod` | — |
| `unknown` | `(reason: str, *, basis: ConceptObservationBasis \| None = None) -> ManifestEvidenceBaseline` | `@classmethod` | — |
| `to_payload` | `() -> dict[str, object]` | — | — |
| `from_payload` | `(value: object, field_name: str) -> ManifestEvidenceBaseline` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ManifestEvidenceBaseline (src/llm_wiki_cli/services/sync_manifest.py)"]
    n1["_mark_untrusted_evidence (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n2["_preserve_unchanged_unknown_baselines (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n3["src/llm_wiki_cli/services/knowledge_index.py"]
    n4["_legacy_operational_state (src/llm_wiki_cli/services/sync_manifest.py)"]
    n5["ManifestEvidenceBaseline.from_basis (src/llm_wiki_cli/services/sync_manifest.py)"]
    n6["ManifestEvidenceBaseline.from_payload (src/llm_wiki_cli/services/sync_manifest.py)"]
    n7["ManifestEvidenceBaseline.unknown (src/llm_wiki_cli/services/sync_manifest.py)"]
    n8["SyncManifest.build_from_inventory (src/llm_wiki_cli/services/sync_manifest.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/sync_manifest.md"
    click n1 "../modules/knowledge_generation.md"
    click n2 "../modules/knowledge_generation.md"
    click n3 "../modules/knowledge_index.md"
    click n4 "../modules/sync_manifest.md"
    click n5 "../modules/sync_manifest.md"
    click n6 "../modules/sync_manifest.md"
    click n7 "../modules/sync_manifest.md"
    click n8 "../modules/sync_manifest.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_manifest](../modules/sync_manifest.md) | 6 | `basis`, `unknown_reason` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_mark_untrusted_evidence` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_preserve_unchanged_unknown_baselines` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `knowledge_index` | import | [knowledge_index](../modules/knowledge_index.md) | — |
| `_legacy_operational_state` | type_reference | [sync_manifest](../modules/sync_manifest.md) | — |
| `ManifestEvidenceBaseline.from_basis` | type_reference | [sync_manifest](../modules/sync_manifest.md) | — |
| `ManifestEvidenceBaseline.from_payload` | type_reference | [sync_manifest](../modules/sync_manifest.md) | — |
| `ManifestEvidenceBaseline.unknown` | type_reference | [sync_manifest](../modules/sync_manifest.md) | — |
| `SyncManifest.build_from_inventory` | type_reference | [sync_manifest](../modules/sync_manifest.md) | — |
