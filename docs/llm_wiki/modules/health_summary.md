# health_summary Module

**Path:** `src/llm_wiki_cli/services/health_summary.py`

## Description

Pure presentation helpers for detailed local and CI health reports.

Summaries distinguish blocking structural integrity, advisory drift, health
classification, separately bound release policy and optional assurance.
Diagnostic previews prioritize actionable causes while retaining exact totals
and routes to complete rows. Captured detail can refine a legacy reason without
changing its stored code or promoting unavailable comparisons to current.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `analysis_compatibility` |
| `.freshness_wording` | `SOURCE_CHANGED_STRUCTURE_UNCHANGED` |
| `.knowledge_observability` | `knowledge_freshness_hint` |
| `__future__` | `annotations` |
| `collections` | `defaultdict` |
| `collections.abc` | `Mapping`, `Sequence` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `re` | `re` |
| `typing` | `Any` |
| `unicodedata` | `unicodedata` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["integrations/github-action/render_summary.py"]
    n1["src/llm_wiki_cli/commands/ci_check_cmd.py"]
    n2["src/llm_wiki_cli/services/analysis_compatibility.py"]
    n3["src/llm_wiki_cli/services/ci_report.py"]
    n4["src/llm_wiki_cli/services/doctor_service.py"]
    n5["src/llm_wiki_cli/services/freshness_wording.py"]
    n6["src/llm_wiki_cli/services/health_summary.py"]
    n7["src/llm_wiki_cli/services/knowledge_observability.py"]
    n8["src/llm_wiki_cli/services/lint_service.py"]
    n0 --> n3
    n0 --> n6
    n1 --> n3
    n1 --> n4
    n1 --> n6
    n1 --> n8
    n3 --> n2
    n3 --> n4
    n3 --> n6
    n3 --> n7
    n3 --> n8
    n4 --> n2
    n4 --> n5
    n4 --> n6
    n4 --> n7
    n4 --> n8
    n6 --> n2
    n6 --> n5
    n6 --> n7
    n7 --> n5
    n8 --> n2
    n8 --> n6
    n8 --> n7
    click n0 "../modules/render_summary.md"
    click n1 "../modules/ci_check_cmd.md"
    click n2 "../modules/analysis_compatibility.md"
    click n3 "../modules/ci_report.md"
    click n4 "../modules/doctor_service.md"
    click n5 "../modules/freshness_wording.md"
    click n6 "../modules/health_summary.md"
    click n7 "../modules/knowledge_observability.md"
    click n8 "../modules/lint_service.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [render_summary](../modules/render_summary.md) |
| Inbound | [ci_check_cmd](../modules/ci_check_cmd.md) |
| Inbound | [ci_report](../modules/ci_report.md) |
| Inbound | [doctor_service](../modules/doctor_service.md) |
| Inbound | [lint_service](../modules/lint_service.md) |
| Outbound | [analysis_compatibility](../modules/analysis_compatibility.md) |
| Outbound | [freshness_wording](../modules/freshness_wording.md) |
| Outbound | [knowledge_observability](../modules/knowledge_observability.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `summary_cell` | `(value: object, limit: int = 240) -> str` | — | Escape inline-code/table content and explicitly disclose UTF-8 clipping. |
| `health_policy` | `(strict: bool) -> str` | — | Describe classification independently of an Action's failure threshold. |
| `optional_status` | `(state: str, *, absent: str) -> str` | — | Disclose optional absence without changing present evidence states. |
| `assurance_rows` | `(report: Mapping) -> list[tuple[str, str]]` | — | Describe captured assurance without inferring adoption or review coverage. |
| `ci_health_rows` | `(report: Mapping, health: Mapping) -> list[tuple[str, str]]` | — | Reuse the captured classification without inferring release admission. |
| `_diagnostic_kind` | `(record: Mapping) -> str` | — | — |
| `_diagnostic_priority` | `(category: str, kind: str) -> int` | — | — |
| `_record_order` | `(record: Mapping) -> tuple[str, ...]` | — | — |
| `diagnostic_groups` | `(records: Sequence[Mapping]) -> list[dict[str, Any]]` | — | Partition emitted records; external grouping needs an exact producer prefix. |
| `diagnostic_preview` | `(records: Sequence[Mapping]) -> dict[str, Any]` | — | Bound examples, keeping duplicate occurrences and exact omitted totals. |
| `_diagnostic_anchor` | `(group: Mapping) -> str` | — | — |
| `_display_hint` | `(record: Mapping, health: Mapping \| None) -> str \| None` | — | — |
| `_legacy_scope_disclosure` | `(record: Mapping) -> str \| None` | — | — |
| `render_validation_markdown` | `(report: Mapping, *, health: Mapping \| None = None) -> str` | — | Present a bounded prefix and complete deterministic rows; never scan source. |
| `freshness_counts` | `(counts: Mapping[str, int] \| None) -> str` | — | Describe existing state counters without inventing model eligibility. |
| `reason_list` | `(reasons: Sequence[str], limit: int = 5) -> str` | — | List a bounded prefix of reported reasons, without estimating counts. |
| `_versions` | `(recorded, live, kind: str, limit: int = 3) -> str` | — | — |
| `captured_analysis_diagnostic` | `(report: Mapping) -> dict \| None` | — | Read validated native commitments, never the current installation. |
| `detailed_health_rows` | `(report: Mapping) -> list[tuple[str, str]]` | — | Describe validated evidence; legacy reports cannot gain inferred detail. |
