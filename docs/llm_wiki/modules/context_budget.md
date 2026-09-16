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
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/config.py"]
    n2["src/llm_wiki_cli/services/change_selection.py"]
    n3["src/llm_wiki_cli/services/context_budget.py"]
    n4["src/llm_wiki_cli/services/context_packet.py"]
    n5["src/llm_wiki_cli/services/context_service.py"]
    n6["src/llm_wiki_cli/services/contracts.py"]
    n7["src/llm_wiki_cli/services/io.py"]
    n8["src/llm_wiki_cli/services/request_json.py"]
    n9["src/llm_wiki_cli/services/task_context.py"]
    n10["src/llm_wiki_cli/services/token_counting.py"]
    n0 --> n1
    n0 --> n3
    n0 --> n4
    n0 --> n5
    n0 --> n6
    n0 --> n9
    n0 --> n10
    n1 --> n7
    n3 --> n1
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n3 --> n7
    n3 --> n8
    n3 --> n10
    n4 --> n1
    n4 --> n2
    n4 --> n5
    n4 --> n6
    n5 --> n1
    n5 --> n2
    n5 --> n3
    n5 --> n4
    n5 --> n6
    n5 --> n7
    n9 --> n1
    n9 --> n2
    n9 --> n3
    n9 --> n4
    n9 --> n5
    n9 --> n7
    n9 --> n8
    n9 --> n10
    click n0 "../modules/api.md"
    click n1 "../modules/config.md"
    click n2 "../modules/change_selection.md"
    click n3 "../modules/context_budget.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/context_service.md"
    click n6 "../modules/services_contracts.md"
    click n7 "../modules/io.md"
    click n8 "../modules/request_json.md"
    click n9 "../modules/task_context.md"
    click n10 "../modules/token_counting.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [context_service](../modules/context_service.md) |
| Inbound | [task_context](../modules/task_context.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [change_selection](../modules/change_selection.md) |
| Outbound | [context_packet](../modules/context_packet.md) |
| Outbound | [context_service](../modules/context_service.md) |
| Outbound | [services_contracts](../modules/services_contracts.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [request_json](../modules/request_json.md) |
| Outbound | [token_counting](../modules/token_counting.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [BudgetedContext](../entities/BudgetedContext.md) | 26 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `validate_request` | `(data: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_accounted_render` | `(render, accounting, counter)` | — | — |
| `fit_payload` | `(payload, request, warnings, counter, *, packet_renderer = None, changes = None, envelope_renderer = None, freshness_rank_by_source = None)` | — | Select whole source entries; keep all enrichment and omission evidence. |
| `build_budgeted_context` | `(src_dir = '.', wiki_dir = DEFAULT_WIKI_DIR, request = None, *, counter: TokenCounter \| None = None, allow_external_src = False, source_selection = None) -> BudgetedContext` | — | — |
| `request_identity` | `(request: Mapping[str, Any]) -> str` | — | — |
| `validate_budgeted_context` | `(rendered: str, request: Mapping[str, Any], *, counter: TokenCounter) -> dict[str, Any]` | — | Independently validate the outer v3 binding, packet and emitted count. |
| `run` | `(args, request = None)` | — | — |