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
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/cli.py"]
    n2["src/llm_wiki_cli/commands/queue_cmd.py"]
    n3["src/llm_wiki_cli/services/context_packet.py"]
    n4["src/llm_wiki_cli/services/documentation_worklist.py"]
    n5["src/llm_wiki_cli/services/inventory_cache.py"]
    n6["src/llm_wiki_cli/services/lint_service.py"]
    n7["src/llm_wiki_cli/services/maintenance_queue.py"]
    n0 --> n3
    n0 --> n7
    n1 --> n2
    n1 --> n6
    n1 --> n7
    n2 --> n7
    n6 --> n5
    n7 --> n3
    n7 --> n4
    n7 --> n5
    n7 --> n6
    click n0 "../modules/api.md"
    click n1 "../modules/cli.md"
    click n2 "../modules/queue_cmd.md"
    click n3 "../modules/context_packet.md"
    click n4 "../modules/documentation_worklist.md"
    click n5 "../modules/inventory_cache.md"
    click n6 "../modules/lint_service.md"
    click n7 "../modules/maintenance_queue.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [cli](../modules/cli.md) |
| Inbound | [queue_cmd](../modules/queue_cmd.md) |
| Outbound | [context_packet](../modules/context_packet.md) |
| Outbound | [documentation_worklist](../modules/documentation_worklist.md) |
| Outbound | [inventory_cache](../modules/inventory_cache.md) |
| Outbound | [lint_service](../modules/lint_service.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `validate_queue_limit` | `(limit: object) -> int` | — | Validate the shared CLI and service bound before reading queue inputs. |
| `compose_queue` | `(pages, work_items, freshness, issues, metrics, *, limit = DEFAULT_QUEUE_LIMIT)` | — | Rank captured evidence; unknown provenance never becomes confirmed drift. |
| `build_maintenance_queue` | `(src_dir = '.', wiki_dir = 'docs/llm_wiki', *, limit = DEFAULT_QUEUE_LIMIT, allow_external_src = False, source_selection = None, helper_cache_dir = None)` | — | — |
| `render_queue` | `(queue)` | — | — |