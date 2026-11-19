# sync_run_options_from_request

**Entry point:** `sync_runtime._sync_run_options_from_request`
**Modules involved:** [host](../modules/host.md), [inventory_cache](../modules/inventory_cache.md), [path_policy](../modules/path_policy.md), [scoped_sync_repair](../modules/scoped_sync_repair.md), [sync_runtime](../modules/sync_runtime.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `inventory_cache.cache_options_for`
2. `inventory_cache.InventoryCacheOptions`
3. `scoped_sync_repair.repair_paths`
4. `scoped_sync_repair.ScopedRepairError`
5. `scoped_sync_repair.ScopedRepairError`
6. `host.emit`
7. `host.emit`
8. `host.emit`
9. `host.emit`
10. `path_policy.validate_source_root`
11. `path_policy.PathValidationError`
12. `path_policy.validate_path`

## Touches

- [host](../modules/host.md)
- [inventory_cache](../modules/inventory_cache.md)
- [path_policy](../modules/path_policy.md)
- [scoped_sync_repair](../modules/scoped_sync_repair.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._sync_run_options_from_request`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
