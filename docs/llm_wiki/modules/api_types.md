# api_types Module

**Path:** `src/llm_wiki_cli/api_types.py`

## Description

Static return contracts for the supported Python API.

These types describe the stable top-level response fields.  Nested extractor,
context, graph, and lifecycle records remain versioned wire payloads and are
therefore represented as ``Any`` where their shape belongs to another
contract.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `typing` | `Any`, `Literal`, `TypedDict` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/api_types.py"]
    n2["src/llm_wiki_cli/services/mcp_server.py"]
    n3["src/llm_wiki_cli/services/native_inspection.py"]
    n0 --> n1
    n0 --> n3
    n2 --> n0
    n2 --> n1
    n3 --> n1
    click n0 "../modules/api.md"
    click n1 "../modules/api_types.md"
    click n2 "../modules/mcp_server.md"
    click n3 "../modules/native_inspection.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [mcp_server](../modules/mcp_server.md) |
| Inbound | [native_inspection](../modules/native_inspection.md) |

## Classes

| Class | Kind | Line | Bases / Target | Description |
|-------|------|------|----------------|-------------|
| [KnowledgeMode](../entities/KnowledgeMode.md) | Type alias | 14 | `Literal['off', 'auto', 'required']` | — |
| [TaskAnchor](../entities/TaskAnchor.md) | Class | 17 | `TypedDict` | — |
| [_RequirementOptions](../entities/RequirementOptions.md) | Class | 22 | `TypedDict` | — |
| [EvidenceRequirement](../entities/EvidenceRequirement.md) | Class | 26 | `_RequirementOptions` | — |
| [TaskStorageOptions](../entities/TaskStorageOptions.md) | Class | 33 | `TypedDict` | Optional selection and proof layout for task request v2. |
| [_TaskOptions](../entities/TaskOptions.md) | Class | 40 | `TypedDict` | — |
| [TaskContextRequest](../entities/TaskContextRequest.md) | Class | 51 | `_TaskOptions` | — |
| [_SearchMatchRanking](../entities/SearchMatchRanking.md) | Class | 55 | `TypedDict` | — |
| [SearchMatch](../entities/SearchMatch.md) | Class | 61 | `_SearchMatchRanking` | — |
| [_SearchMetadata](../entities/SearchMetadata.md) | Class | 70 | `TypedDict` | — |
| [SearchResult](../entities/SearchResult.md) | Class | 81 | `_SearchMetadata` | — |
| [MaintenanceQueueResult](../entities/MaintenanceQueueResult.md) | Class | 92 | `TypedDict` | — |
| [MaintenanceRecordResult](../entities/MaintenanceRecordResult.md) | Class | 107 | `TypedDict` | — |
| [MaintenanceStatusResult](../entities/MaintenanceStatusResult.md) | Class | 126 | `TypedDict` | — |
| [_MaintenanceAdoptionOptions](../entities/MaintenanceAdoptionOptions.md) | Class | 141 | `TypedDict` | — |
| [MaintenanceAdoptionResult](../entities/MaintenanceAdoptionResult.md) | Class | 149 | `_MaintenanceAdoptionOptions` | — |
| [MaintenanceAcknowledgmentResult](../entities/MaintenanceAcknowledgmentResult.md) | Class | 154 | `TypedDict` | — |
| [MaintenanceRecoveryResult](../entities/MaintenanceRecoveryResult.md) | Class | 164 | `TypedDict` | — |
| [KnowledgeCoverageCounts](../entities/KnowledgeCoverageCounts.md) | Class | 172 | `TypedDict` | — |
| [KnowledgeCoverageResult](../entities/KnowledgeCoverageResult.md) | Class | 180 | `TypedDict` | Versioned aggregate diagnostics without identities or raw evidence. |
| [ResultBounds](../entities/ResultBounds.md) | Class | 193 | `TypedDict` | Exact size disclosure for one bounded result collection. |
| [ByteResultBounds](../entities/ByteResultBounds.md) | Class | 201 | `ResultBounds` | Serialized-byte bound with its independent hard limit. |
| [KnowledgeStatus](../entities/KnowledgeStatus.md) | Class | 207 | `TypedDict` | Compact availability and freshness status shared by query adapters. |
| [ContextKnowledgeSelection](../entities/ContextKnowledgeSelection.md) | Class | 216 | `TypedDict` | Bounded inert content selected by explicit knowledge mode. |
| [_ContextKnowledgeRequired](../entities/ContextKnowledgeRequired.md) | Class | 225 | `TypedDict` | — |
| [ContextKnowledgeResult](../entities/ContextKnowledgeResult.md) | Class | 236 | `_ContextKnowledgeRequired` | Canonical explicit-mode knowledge outcome. |
| [RankingPolicy](../entities/RankingPolicy.md) | Class | 242 | `TypedDict` | Disclosure for optional current-first budget ranking. |
| [RequiredKnowledgeErrorDetails](../entities/RequiredKnowledgeErrorDetails.md) | Class | 253 | `TypedDict` | Stable details attached to required-mode interface failures. |
| [_ExtractSourceRequired](../entities/ExtractSourceRequired.md) | Class | 266 | `TypedDict` | — |
| [ExtractSourceResult](../entities/ExtractSourceResult.md) | Class | 272 | `_ExtractSourceRequired` | Top-level ``extract_source`` payload. |
| [_ContextRequired](../entities/ContextRequired.md) | Class | 284 | `TypedDict` | — |
| [ContextPayload](../entities/ContextPayload.md) | Class | 294 | `_ContextRequired` | Top-level JSON context payload. |
| [MarkdownContextResult](../entities/MarkdownContextResult.md) | Class | 305 | `TypedDict` | Markdown rendering plus its source context payload. |
| [WikiPage](../entities/api_types_WikiPage.md) | Class | 313 | `TypedDict` | One registry-backed wiki page. |
| [WikiPageCounts](../entities/WikiPageCounts.md) | Class | 325 | `TypedDict` | Counts returned with a wiki-page listing. |
| [WikiPagesResult](../entities/WikiPagesResult.md) | Class | 333 | `TypedDict` | Top-level ``list_wiki_pages`` payload. |
| [_BoundedQueryResult](../entities/BoundedQueryResult.md) | Class | 341 | `TypedDict` | Fields shared by bounded documentation graph queries. |
| [FlowForEntrypointResult](../entities/FlowForEntrypointResult.md) | Class | 352 | `_BoundedQueryResult` | — |
| [DataFlowForEntrypointResult](../entities/DataFlowForEntrypointResult.md) | Class | 356 | `_BoundedQueryResult` | — |
| [_StaticCallQueryOptions](../entities/StaticCallQueryOptions.md) | Class | 360 | `TypedDict` | Additive captured-source coverage for static call queries. |
| [CallersResult](../entities/CallersResult.md) | Class | 366 | `_BoundedQueryResult`, `_StaticCallQueryOptions` | — |
| [CalleesResult](../entities/CalleesResult.md) | Class | 371 | `_BoundedQueryResult`, `_StaticCallQueryOptions` | — |
| [DependencyNeighborhoodResult](../entities/DependencyNeighborhoodResult.md) | Class | 376 | `_BoundedQueryResult` | — |
| [PagesForSymbolResult](../entities/PagesForSymbolResult.md) | Class | 386 | `_BoundedQueryResult` | — |
| [ConceptResult](../entities/ConceptResult.md) | Class | 391 | `_BoundedQueryResult` | — |
| [ConceptSectionsResult](../entities/ConceptSectionsResult.md) | Class | 398 | `ConceptResult` | — |
| [RelatedConceptsResult](../entities/RelatedConceptsResult.md) | Class | 404 | `ConceptResult` | — |
| [TypedGraphTraversalResult](../entities/TypedGraphTraversalResult.md) | Class | 413 | `ConceptResult` | — |
| [EvidenceExplanationResult](../entities/EvidenceExplanationResult.md) | Class | 423 | `ConceptResult` | — |
| [QueryCostDisclosure](../entities/QueryCostDisclosure.md) | Class | 427 | `TypedDict` | Deterministic disclosure of work selected for a query. |
| [_DocumentationQueryRequired](../entities/DocumentationQueryRequired.md) | Class | 439 | `TypedDict` | — |
| [DocumentationQueryResult](../entities/DocumentationQueryResult.md) | Class | 451 | `_DocumentationQueryRequired` | Common envelope returned by the shared bounded query dispatcher. |
| [DocumentationExportResult](../entities/DocumentationExportResult.md) | Class | 488 | `TypedDict` | Top-level documentation export and verification report. |
| [DoctorAvailability](../entities/DoctorAvailability.md) | Class | 512 | `TypedDict` | — |
| [DoctorFreshness](../entities/DoctorFreshness.md) | Class | 518 | `TypedDict` | — |
| [DoctorSnapshotParity](../entities/DoctorSnapshotParity.md) | Class | 525 | `TypedDict` | — |
| [DoctorGovernance](../entities/DoctorGovernance.md) | Class | 531 | `TypedDict` | — |
| [DoctorDrift](../entities/DoctorDrift.md) | Class | 540 | `TypedDict` | — |
| [DoctorVerificationReceipt](../entities/DoctorVerificationReceipt.md) | Class | 550 | `TypedDict` | — |
| [DoctorResult](../entities/DoctorResult.md) | Class | 557 | `TypedDict` | Stable ``llm-wiki-doctor/v1`` Python API payload. |
| [HealthSelection](../entities/HealthSelection.md) | Class | 576 | `TypedDict` | — |
| [HealthScope](../entities/HealthScope.md) | Class | 582 | `TypedDict` | — |
| [HealthEvaluation](../entities/HealthEvaluation.md) | Class | 588 | `TypedDict` | — |
| [HealthSnapshot](../entities/HealthSnapshot.md) | Class | 593 | `TypedDict` | — |
| [HealthComponent](../entities/HealthComponent.md) | Class | 603 | `TypedDict` | — |
| [HealthProducer](../entities/HealthProducer.md) | Class | 610 | `TypedDict` | — |
| [HealthComparisonBasis](../entities/HealthComparisonBasis.md) | Class | 618 | `TypedDict` | — |
| [HealthCoverage](../entities/HealthCoverage.md) | Class | 625 | `TypedDict` | — |
| [HealthReason](../entities/HealthReason.md) | Class | 635 | `TypedDict` | — |
| [HealthDetails](../entities/HealthDetails.md) | Class | 642 | `TypedDict` | — |
| [DoctorV3Result](../entities/DoctorV3Result.md) | Class | 652 | `DoctorResult` | Opt-in health report with captured coverage and comparison evidence. |
| [ComparisonPolicy](../entities/ComparisonPolicy.md) | Type alias | 657 | `Literal['auto', 'exact-v1', 'analysis-v1']` | — |
| [AnalysisCompatibilityRecord](../entities/AnalysisCompatibilityRecord.md) | Class | 660 | `TypedDict` | — |
| [AnalysisComparisonContract](../entities/AnalysisComparisonContract.md) | Class | 671 | `TypedDict` | — |
| [AnalysisComparisonDecision](../entities/AnalysisComparisonDecision.md) | Class | 677 | `TypedDict` | — |
| [HealthComparisonBasisV2](../entities/HealthComparisonBasisV2.md) | Class | 683 | `TypedDict` | — |
| [HealthDetailsV2](../entities/HealthDetailsV2.md) | Class | 691 | `TypedDict` | — |
| [DoctorV4Result](../entities/DoctorV4Result.md) | Class | 701 | `DoctorResult` | Compatibility-aware health with versioned captured comparison evidence. |
| [_NativeInspectionMaintenance](../entities/NativeInspectionMaintenance.md) | Class | 706 | `TypedDict` | — |
| [NativeInspectionResult](../entities/NativeInspectionResult.md) | Class | 710 | `_NativeInspectionMaintenance` | Bounded component results sharing one source/wiki read scope. |
