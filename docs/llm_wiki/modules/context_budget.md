# context_budget Module

**Path:** `src/llm_wiki_cli/services/context_budget.py`

## Description

Implements opt-in v3 budgets for the complete emitted JSON, Markdown, or packet
representation, including metadata and omission evidence. It progressively
reduces whole source entries and reports `cannot-fit` when required evidence
alone exceeds the budget. Accounting identifies the host-supplied counter and
excludes host chat framing.

Context construction reuses one captured source/wiki read, retains explicit
change provenance, and revalidates that basis before returning the rendered
result. Exact mode requires a trusted exact counter; estimated mode labels its
weaker accounting explicitly.

Packet fitting measures internal candidates before applying final wire limits,
then independently validates the selected packet and complete-output accounting.
The built-in UTF-8 estimator can skip full rendering when the unchanged source
JSON fragment alone already exceeds the entire delivery allowance. Custom and
exact counters retain full-render fitting without assuming monotonic token cost.

The CLI adapter handles typed ordinary-authority refusal through the shared packet error renderer. It emits the same bounded cause/recovery requirements on stderr, leaves stdout and existing output files untouched, and performs no repair or fallback promotion. This failure remains distinct from a valid result that cannot fit its budget.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `context_packet`, `context_service` |
| `..config` | `DEFAULT_WIKI_DIR` |
| `.change_selection` | `affected_page_map`, `changes_from_args`, `select_changes`, `validate_changes` |
| `.contracts` | `CONTEXT_BUDGET_PROTOCOL_VERSION` |
| `.io` | `write_text_output`, `write_utf8_stdout` |
| `.request_json` | `_pairs`, `_constant` |
| `.token_counting` | `EstimatedCounter`, `LocalTokenizerCounter`, `TokenCounter` |
| `__future__` | `annotations` |
| `copy` | `copy` |
| `dataclasses` | `dataclass`, `replace` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `sys` | `sys` |
| `typing` | `Any`, `Mapping` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/context_budget.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/context_budget.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (6) |
| Outbound | `src` (8) |

> All 13 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [BudgetedContext](../entities/BudgetedContext.md) | 26 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `validate_request` | `(data: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_accounted_render` | `(render, accounting, counter)` | — | — |
| `fit_payload` | `(payload, request, warnings, counter, *, packet_renderer = None, changes = None, envelope_renderer = None, freshness_rank_by_source = None, source_json_lower_bound = False)` | — | Select whole source entries; keep all enrichment and omission evidence. |
| `build_budgeted_context` | `(src_dir = '.', wiki_dir = DEFAULT_WIKI_DIR, request = None, *, counter: TokenCounter \| None = None, allow_external_src = False, source_selection = None) -> BudgetedContext` | — | — |
| `request_identity` | `(request: Mapping[str, Any]) -> str` | — | — |
| `validate_budgeted_context` | `(rendered: str, request: Mapping[str, Any], *, counter: TokenCounter) -> dict[str, Any]` | — | Independently validate the outer v3 binding, packet and emitted count. |
| `run` | `(args, request = None)` | — | — |