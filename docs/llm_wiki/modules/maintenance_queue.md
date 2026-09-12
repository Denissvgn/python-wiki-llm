# maintenance_queue Module

**Path:** `src/llm_wiki_cli/services/maintenance_queue.py`

## Description

Ranks managed wiki pages using captured freshness, semantic work items, lint
findings, reachability, and source fan-in. Each bounded queue item explains its
priority, distinguishes actionable from informational evidence, and identifies
the editable semantic section. Unknown provenance stays explicit; queue
construction preserves the captured source/wiki basis and does not edit pages.

## Imports

| Source | Symbols |
|--------|---------|
| `.context_packet` | `capture_context_read`, `_assert_source_unchanged`, `_assert_wiki_unchanged`, `_assert_selection_unchanged` |
| `.documentation_worklist` | `build_documentation_worklist` |
| `.inventory_cache` | `InventoryCacheOptions` |
| `.lint_service` | `build_report` |
| `__future__` | `annotations` |
| `dataclasses` | `asdict` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `pathlib` | `Path` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/queue_cmd.py"]
    n1["src/llm_wiki_cli/services/context_packet.py"]
    n2["src/llm_wiki_cli/services/documentation_worklist.py"]
    n3["src/llm_wiki_cli/services/inventory_cache.py"]
    n4["src/llm_wiki_cli/services/lint_service.py"]
    n5["src/llm_wiki_cli/services/maintenance_queue.py"]
    n0 --> n5
    n4 --> n3
    n5 --> n1
    n5 --> n2
    n5 --> n3
    n5 --> n4
    click n0 "../modules/queue_cmd.md"
    click n1 "../modules/context_packet.md"
    click n2 "../modules/documentation_worklist.md"
    click n3 "../modules/inventory_cache.md"
    click n4 "../modules/lint_service.md"
    click n5 "../modules/maintenance_queue.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [queue_cmd](../modules/queue_cmd.md) |
| Outbound | [context_packet](../modules/context_packet.md) |
| Outbound | [documentation_worklist](../modules/documentation_worklist.md) |
| Outbound | [inventory_cache](../modules/inventory_cache.md) |
| Outbound | [lint_service](../modules/lint_service.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `compose_queue` | `(pages, work_items, freshness, issues, metrics, *, limit = 30)` | — | Rank captured evidence; unknown provenance never becomes confirmed drift. |
| `build_maintenance_queue` | `(src_dir = '.', wiki_dir = 'docs/llm_wiki', *, limit = 30, allow_external_src = False, source_selection = None, helper_cache_dir = None)` | — | — |
| `render_queue` | `(queue)` | — | — |
