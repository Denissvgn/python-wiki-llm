# maintenance_queue Module

**Path:** `src/llm_wiki_cli/services/maintenance_queue.py`

## Description

Ranks managed wiki pages using captured freshness, semantic work items, lint
findings, reachability, and source fan-in. Each bounded queue item explains its
priority, distinguishes actionable from informational evidence, and identifies
the editable semantic section. Unknown provenance stays explicit; queue
construction preserves the captured source/wiki basis and does not edit pages.

For a coherent unadopted native wiki, the same captured inventory and verified
page mappings identify source-backed semantic sections that lack ordinary review
custody. Their exact section locators appear as bounded informational coverage
gaps even after owning sync makes structural freshness current. This keeps
retained authored claims visible for source/prose inspection without inventing
pending records, acknowledgments or a verdict about their correctness. Corrected
prose remains untracked until explicit adoption and review.

## Imports

| Source | Symbols |
|--------|---------|
| `.context_packet_builder` | `capture_context_read`, `_assert_source_unchanged`, `_assert_wiki_unchanged`, `_assert_selection_unchanged` |
| `.documentation_worklist` | `build_documentation_worklist` |
| `.inventory_cache` | `InventoryCacheOptions` |
| `.lint_service` | `build_report` |
| `.maintenance_service` | `capture_maintenance_observations` |
| `__future__` | `annotations` |
| `collections` | `Counter` |
| `dataclasses` | `asdict` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `llm_wiki_engine.knowledge_storage` | `canonical_bytes`, `canonical_bytes` |
| `llm_wiki_engine.maintenance_status` | `compact_maintenance_summary`, `build_maintenance_status` |
| `pathlib` | `Path` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/cli_declarations.py"]
    n2["src/llm_wiki_cli/commands/queue_cmd.py"]
    n3["src/llm_wiki_cli/services/context_packet_builder.py"]
    n4["src/llm_wiki_cli/services/documentation_worklist.py"]
    n5["src/llm_wiki_cli/services/inventory_cache.py"]
    n6["src/llm_wiki_cli/services/lint_service.py"]
    n7["src/llm_wiki_cli/services/maintenance_queue.py"]
    n8["src/llm_wiki_cli/services/maintenance_service.py"]
    n9["src/llm_wiki_cli/services/mcp_server.py"]
    n10["src/llm_wiki_engine/knowledge_storage.py"]
    n11["src/llm_wiki_engine/maintenance_status.py"]
    n0 --> n3
    n0 --> n6
    n0 --> n7
    n0 --> n8
    n0 --> n10
    n1 --> n7
    n2 --> n7
    n3 --> n11
    n6 --> n5
    n7 --> n3
    n7 --> n4
    n7 --> n5
    n7 --> n6
    n7 --> n8
    n7 --> n10
    n7 --> n11
    n8 --> n3
    n8 --> n10
    n8 --> n11
    n9 --> n0
    n9 --> n3
    n9 --> n6
    n9 --> n7
    n11 --> n10
    click n0 "../modules/api.md"
    click n1 "../modules/cli_declarations.md"
    click n2 "../modules/queue_cmd.md"
    click n3 "../modules/context_packet_builder.md"
    click n4 "../modules/documentation_worklist.md"
    click n5 "../modules/inventory_cache.md"
    click n6 "../modules/lint_service.md"
    click n7 "../modules/maintenance_queue.md"
    click n8 "../modules/maintenance_service.md"
    click n9 "../modules/mcp_server.md"
    click n10 "../modules/knowledge_storage.md"
    click n11 "../modules/maintenance_status.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [cli_declarations](../modules/cli_declarations.md) |
| Inbound | [queue_cmd](../modules/queue_cmd.md) |
| Inbound | [mcp_server](../modules/mcp_server.md) |
| Outbound | [context_packet_builder](../modules/context_packet_builder.md) |
| Outbound | [documentation_worklist](../modules/documentation_worklist.md) |
| Outbound | [inventory_cache](../modules/inventory_cache.md) |
| Outbound | [lint_service](../modules/lint_service.md) |
| Outbound | [maintenance_service](../modules/maintenance_service.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [maintenance_status](../modules/maintenance_status.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `validate_queue_limit` | `(limit: object) -> int` | — | Validate the shared CLI and service bound before reading queue inputs. |
| `_ordinary_review_custody` | `(maintenance_report, manifest_basis)` | — | Qualify existing captured authority without another read or adoption. |
| `compose_queue` | `(pages, work_items, freshness, issues, metrics, *, limit = DEFAULT_QUEUE_LIMIT, maintenance_report = None, manifest_basis = None)` | — | Rank captured evidence; unknown provenance never becomes confirmed drift. |
| `build_maintenance_queue` | `(src_dir = '.', wiki_dir = 'docs/llm_wiki', *, limit = DEFAULT_QUEUE_LIMIT, allow_external_src = False, source_selection = None, helper_cache_dir = None)` | — | — |
| `render_queue` | `(queue)` | — | — |
