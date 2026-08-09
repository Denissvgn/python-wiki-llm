# KnowledgeReadView

**Location:** `src/llm_wiki_cli/services/knowledge_consumption.py:288`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_consumption](../modules/knowledge_consumption.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Validated, immutable-by-contract state for one native read operation.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `availability` | `KnowledgeAvailability` | *required* | — |
| `mode` | `KnowledgeReadMode` | *required* | — |
| `reason` | `KnowledgeReadReason` | *required* | — |
| `surface` | `Mapping[str, Any] \| None` | *required* | — |
| `knowledge` | `KnowledgeIndex \| None` | *required* | — |
| `manifest_basis` | `SyncManifest \| None` | *required* | — |
| `freshness` | `KnowledgeFreshnessReport \| None` | *required* | — |
| `counts` | `KnowledgeReadCounts \| None` | *required* | — |
| `projection_findings` | `tuple[KnowledgeLoadIssue, ...]` | *required* | — |
| `load_state` | `KnowledgeLoadState` | *required* | — |
| `underlying_load_state` | `KnowledgeLoadState \| None` | `None` | — |
| `machine_verification` | `MachineVerificationReadView` | `field(default_factory=MachineVerificationReadView)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `reason_code` | `() -> str` | `@property` | — |
| `ready` | `() -> bool` | `@property` | — |
| `knowledge_available` | `() -> bool` | `@property` | — |
| `freshness_evaluated` | `() -> bool` | `@property` | — |
| `surface_payload` | `() -> Mapping[str, Any] \| None` | `@property` | — |
| `knowledge_index` | `() -> KnowledgeIndex \| None` | `@property` | — |
| `manifest` | `() -> SyncManifest \| None` | `@property` | — |
| `findings` | `() -> tuple[KnowledgeLoadIssue, ...]` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeReadView (src/llm_wiki_cli/services/knowledge_consumption.py)"]
    n1["_freshness_basis (src/llm_wiki_cli/services/context_packet.py)"]
    n2["_build_context_knowledge_view (src/llm_wiki_cli/services/context_service.py)"]
    n3["_context_query_surface (src/llm_wiki_cli/services/context_service.py)"]
    n4["_knowledge_error_view (src/llm_wiki_cli/services/context_service.py)"]
    n5["_availability_section (src/llm_wiki_cli/services/doctor_service.py)"]
    n6["_diagnostic_freshness_states (src/llm_wiki_cli/services/doctor_service.py)"]
    n7["_drift_section (src/llm_wiki_cli/services/doctor_service.py)"]
    n8["_freshness_section (src/llm_wiki_cli/services/doctor_service.py)"]
    n9["_governance_section (src/llm_wiki_cli/services/doctor_service.py)"]
    n10["_snapshot_section (src/llm_wiki_cli/services/doctor_service.py)"]
    n11["_verification_section (src/llm_wiki_cli/services/doctor_service.py)"]
    n12["src/llm_wiki_cli/services/documentation_native.py"]
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
    click n0 "../modules/knowledge_consumption.md"
    click n1 "../modules/context_packet.md"
    click n2 "../modules/context_service.md"
    click n3 "../modules/context_service.md"
    click n4 "../modules/context_service.md"
    click n5 "../modules/doctor_service.md"
    click n6 "../modules/doctor_service.md"
    click n7 "../modules/doctor_service.md"
    click n8 "../modules/doctor_service.md"
    click n9 "../modules/doctor_service.md"
    click n10 "../modules/doctor_service.md"
    click n11 "../modules/doctor_service.md"
    click n12 "../modules/documentation_native.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_consumption](../modules/knowledge_consumption.md) | 9 | `availability`, `counts`, `freshness`, `knowledge`, `load_state`, `machine_verification`, `manifest_basis`, `mode`, `projection_findings`, `reason`, `surface`, `underlying_load_state` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_freshness_basis` | type_reference | [context_packet](../modules/context_packet.md) |
| `_build_context_knowledge_view` | type_reference | [context_service](../modules/context_service.md) |
| `_context_query_surface` | type_reference | [context_service](../modules/context_service.md) |
| `_knowledge_error_view` | type_reference | [context_service](../modules/context_service.md) |
| `_availability_section` | type_reference | [doctor_service](../modules/doctor_service.md) |
| `_diagnostic_freshness_states` | type_reference | [doctor_service](../modules/doctor_service.md) |
| `_drift_section` | type_reference | [doctor_service](../modules/doctor_service.md) |
| `_freshness_section` | type_reference | [doctor_service](../modules/doctor_service.md) |
| `_governance_section` | type_reference | [doctor_service](../modules/doctor_service.md) |
| `_snapshot_section` | type_reference | [doctor_service](../modules/doctor_service.md) |
| `_verification_section` | type_reference | [doctor_service](../modules/doctor_service.md) |
| `documentation_native` | import | [documentation_native](../modules/documentation_native.md) |
