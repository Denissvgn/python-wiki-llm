"""Static return contracts for the supported Python API.

These types describe the stable top-level response fields.  Nested extractor,
context, graph, and lifecycle records remain versioned wire payloads and are
therefore represented as ``Any`` where their shape belongs to another
contract.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict


KnowledgeMode = Literal["off", "auto", "required"]


class ResultBounds(TypedDict):
    """Exact size disclosure for one bounded result collection."""

    total: int
    returned: int
    truncated: bool


class ByteResultBounds(ResultBounds):
    """Serialized-byte bound with its independent hard limit."""

    limit: int


class KnowledgeStatus(TypedDict):
    """Compact availability and freshness status shared by query adapters."""

    availability: str
    reason: str
    freshness: str
    freshness_evaluated: bool


class ContextKnowledgeSelection(TypedDict):
    """Bounded inert content selected by explicit knowledge mode."""

    concepts: list[dict[str, Any]]
    pages: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    relationship_coverage: dict[str, Any]


class _ContextKnowledgeRequired(TypedDict):
    mode: KnowledgeMode
    status: str
    availability: str
    reason: str
    selected: bool
    freshness_evaluated: bool
    bounds: dict[str, ResultBounds]
    fallback: dict[str, Any]


class ContextKnowledgeResult(_ContextKnowledgeRequired, total=False):
    """Canonical explicit-mode knowledge outcome."""

    selection: ContextKnowledgeSelection


class RankingPolicy(TypedDict):
    """Disclosure for optional current-first budget ranking."""

    requested: bool
    policy: str
    scope: str
    budget_pressure: bool
    applied: bool
    reason: str


class RequiredKnowledgeErrorDetails(TypedDict):
    """Stable details attached to required-mode interface failures."""

    code: str
    field: str
    mode: str
    availability: str
    reason: str
    fallback_evidence: list[str]
    recovery_command: str
    mutation_permitted: bool


class _ExtractSourceRequired(TypedDict):
    schema_version: str
    inventory: dict[str, dict[str, Any]]
    data_flow_details: dict[str, Any]


class ExtractSourceResult(_ExtractSourceRequired, total=False):
    """Top-level ``extract_source`` payload."""

    docker: dict[str, Any]
    unsupported_sources: dict[str, Any]
    entrypoints: list[dict[str, Any]]
    data_flows: list[dict[str, Any]]
    dependencies: dict[str, Any]
    api_contracts: dict[str, Any]
    warnings: list[str]


class _ContextRequired(TypedDict):
    budget: int
    used: int
    truncated: bool
    omitted_files: list[str]
    downgraded_files: dict[str, str]
    bounds: dict[str, Any]
    files: dict[str, Any]


class ContextPayload(_ContextRequired, total=False):
    """Top-level JSON context payload."""

    graphs: dict[str, Any]
    knowledge: ContextKnowledgeResult | dict[str, Any]
    typed_graph: dict[str, Any]
    surface: dict[str, Any]
    ranking_policy: RankingPolicy | dict[str, Any]
    warnings: list[str]


class MarkdownContextResult(TypedDict):
    """Markdown rendering plus its source context payload."""

    content: str
    payload: ContextPayload
    warnings: list[str]


class WikiPage(TypedDict):
    """One registry-backed wiki page."""

    kind: str
    id: str
    label: str
    canonical_path: str
    mcp_uri: str
    role: str
    obsidian_mirror_dir: str | None


class WikiPageCounts(TypedDict):
    """Counts returned with a wiki-page listing."""

    total: int
    by_kind: dict[str, int]
    architecture_pages: int


class WikiPagesResult(TypedDict):
    """Top-level ``list_wiki_pages`` payload."""

    wiki_dir: str
    counts: WikiPageCounts
    pages: list[WikiPage]


class _BoundedQueryResult(TypedDict):
    """Fields shared by bounded documentation graph queries."""

    query: str
    found: bool
    ambiguous: bool
    matches: list[dict[str, Any]]
    truncated: bool
    bounds: dict[str, Any]


class FlowForEntrypointResult(_BoundedQueryResult):
    flow: dict[str, Any] | None


class DataFlowForEntrypointResult(_BoundedQueryResult):
    data_flow: dict[str, Any] | None


class CallersResult(_BoundedQueryResult):
    callable: dict[str, Any] | None
    callers: list[dict[str, Any]]


class CalleesResult(_BoundedQueryResult):
    callable: dict[str, Any] | None
    callees: list[dict[str, Any]]


class DependencyNeighborhoodResult(_BoundedQueryResult):
    path: str | None
    inbound: list[str]
    outbound: list[str]
    metrics: dict[str, Any]
    cycle_groups: list[dict[str, Any]]
    load_order_index: int | None
    pages: list[dict[str, Any]]


class PagesForSymbolResult(_BoundedQueryResult):
    symbol: dict[str, Any] | None
    pages: list[dict[str, Any]]


class ConceptResult(_BoundedQueryResult):
    knowledge: KnowledgeStatus | dict[str, Any]
    concept: dict[str, Any] | None
    total: int
    returned: int


class ConceptSectionsResult(ConceptResult):
    section_ownership: dict[str, Any]
    ownership: str | None
    sections: list[dict[str, Any]]


class RelatedConceptsResult(ConceptResult):
    direction: str
    kinds: list[str]
    relationships: list[dict[str, Any]]
    related_concepts: list[dict[str, Any]]
    unresolved_targets: list[dict[str, Any]]
    external_targets: list[dict[str, Any]]


class TypedGraphTraversalResult(ConceptResult):
    direction: str
    kinds: list[str]
    origins: list[str]
    resolutions: list[str]
    include_evidence: bool
    typed_graph: dict[str, Any]
    edges: list[dict[str, Any]]


class EvidenceExplanationResult(ConceptResult):
    evidence: dict[str, Any] | None


class QueryCostDisclosure(TypedDict):
    """Deterministic disclosure of work selected for a query."""

    scope: Literal[
        "snapshot-index-only",
        "targeted-extraction",
        "full-inventory",
    ]
    full_inventory_performed: bool
    supplied_paths: int


class _DocumentationQueryRequired(TypedDict):
    schema_version: str
    operation: str
    query: Any
    found: bool
    ambiguous: bool
    matches: list[dict[str, Any]]
    bounds: dict[str, ResultBounds | ByteResultBounds]
    truncated: bool
    cost: QueryCostDisclosure


class DocumentationQueryResult(_DocumentationQueryRequired, total=False):
    """Common envelope returned by the shared bounded query dispatcher."""

    knowledge: KnowledgeStatus | dict[str, Any]
    concept: dict[str, Any] | None
    total: int
    returned: int
    direction: str
    kinds: list[str]
    relationships: list[dict[str, Any]]
    related_concepts: list[dict[str, Any]]
    unresolved_targets: list[dict[str, Any]]
    external_targets: list[dict[str, Any]]
    origins: list[str]
    resolutions: list[str]
    include_evidence: bool
    typed_graph: dict[str, Any]
    edges: list[dict[str, Any]]
    symbol: dict[str, Any] | None
    pages: list[dict[str, Any]]
    callers: list[dict[str, Any]]
    callees: list[dict[str, Any]]
    flow: dict[str, Any] | None
    data_flow: dict[str, Any] | None
    path: str | None
    inbound: list[str]
    outbound: list[str]
    metrics: dict[str, Any]
    cycle_groups: list[dict[str, Any]]
    load_order_index: int | None
    impacted_paths: list[str]
    concepts: list[dict[str, Any]]
    limitations: list[str]
    raw_evidence: list[dict[str, Any]]


class DocumentationExportResult(TypedDict):
    """Top-level documentation export and verification report."""

    schema_version: str
    run_id: str
    state: str
    verdict: str
    source: dict[str, Any]
    baseline: dict[str, Any]
    intake: dict[str, Any]
    skills: list[dict[str, Any]]
    coverage: dict[str, Any]
    budgets: dict[str, Any]
    evidence: dict[str, Any]
    execution_route: dict[str, Any]
    unresolved_findings: list[dict[str, Any]]
    validation: dict[str, Any]
    limitations: list[str]
    distribution: dict[str, Any]
    deployment_handoff: dict[str, Any]
    resume: dict[str, Any]
    generated_at: str


class DoctorAvailability(TypedDict):
    state: str
    reason: str
    usable: bool


class DoctorFreshness(TypedDict):
    evaluated: bool
    disclosure: str
    concepts: int
    counts_by_state: dict[str, int] | None


class DoctorSnapshotParity(TypedDict):
    state: str
    issue_count: int
    reasons: list[str]


class DoctorGovernance(TypedDict):
    state: str
    ledger: str
    projection: str
    expired_reviews: int
    issue_count: int
    reasons: list[str]


class DoctorDrift(TypedDict):
    state: str
    confirmed_stale: int
    indeterminate: int
    nonsemantic_changes: int
    counts_by_state: dict[str, int] | None
    diagnostic_count: int
    reasons: list[str]


class DoctorVerificationReceipt(TypedDict):
    state: str
    reason: str
    recorded_result: str | None
    passed: bool | None


class DoctorResult(TypedDict):
    """Stable ``llm-wiki-doctor/v1`` Python API payload."""

    schema_version: str
    status: str
    exit_code: int
    strict: bool
    wiki_dir: str
    src_dir: str
    availability: DoctorAvailability
    freshness: DoctorFreshness
    snapshot_parity: DoctorSnapshotParity
    governance: DoctorGovernance
    drift: DoctorDrift
    verification_receipt: DoctorVerificationReceipt
    degraded_reasons: list[str]
    unhealthy_reasons: list[str]


__all__ = [
    "ByteResultBounds",
    "CalleesResult",
    "CallersResult",
    "ConceptResult",
    "ConceptSectionsResult",
    "ContextKnowledgeResult",
    "ContextKnowledgeSelection",
    "ContextPayload",
    "DataFlowForEntrypointResult",
    "DependencyNeighborhoodResult",
    "DocumentationQueryResult",
    "DocumentationExportResult",
    "DoctorAvailability",
    "DoctorDrift",
    "DoctorFreshness",
    "DoctorGovernance",
    "DoctorResult",
    "DoctorSnapshotParity",
    "DoctorVerificationReceipt",
    "EvidenceExplanationResult",
    "ExtractSourceResult",
    "FlowForEntrypointResult",
    "MarkdownContextResult",
    "KnowledgeMode",
    "KnowledgeStatus",
    "PagesForSymbolResult",
    "QueryCostDisclosure",
    "RankingPolicy",
    "RelatedConceptsResult",
    "RequiredKnowledgeErrorDetails",
    "ResultBounds",
    "TypedGraphTraversalResult",
    "WikiPage",
    "WikiPageCounts",
    "WikiPagesResult",
]
