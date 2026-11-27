# verify_written_wiki

**Entry point:** `sync_runtime._verify_written_wiki`
**Modules involved:** [host](../modules/host.md), [inventory_cache](../modules/inventory_cache.md), [lint_service](../modules/lint_service.md), [sync_runtime](../modules/sync_runtime.md)

> Run the strict checks once on the wiki this sync just wrote.

The checks use the request's own source selection, helpers and inventory
cache, so the source is not analysed a second time when the cache holds
the sync's extraction.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `host.emit`
2. `lint_service.build_report`
3. `inventory_cache.cache_options_for`
4. `host.emit`
5. `lint_service.render_text`
6. `host.emit`
7. `host.emit`

## Touches

- [host](../modules/host.md)
- [inventory_cache](../modules/inventory_cache.md)
- [lint_service](../modules/lint_service.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._verify_written_wiki`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
