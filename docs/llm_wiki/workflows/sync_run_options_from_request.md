# sync_run_options_from_request

**Entry point:** `sync_runtime._sync_run_options_from_request`
**Modules involved:** [historical_retirement](../modules/historical_retirement.md), [host](../modules/host.md), [inventory_cache](../modules/inventory_cache.md), [knowledge_evidence](../modules/knowledge_evidence.md), [path_policy](../modules/path_policy.md), [scoped_sync_repair](../modules/scoped_sync_repair.md), [source_retirement](../modules/source_retirement.md), [sync_runtime](../modules/sync_runtime.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `inventory_cache.cache_options_for`
2. `inventory_cache.InventoryCacheOptions`
3. `scoped_sync_repair.repair_paths`
4. `historical_retirement.selected_sources`
5. `historical_retirement.selected_pages`
6. `historical_retirement.selected_pages`
7. `knowledge_evidence.is_valid_sha256`
8. `source_retirement.SourceRetirementError`
9. `source_retirement.SourceRetirementError`
10. `source_retirement.SourceRetirementError`
11. `scoped_sync_repair.ScopedRepairError`
12. `scoped_sync_repair.ScopedRepairError`
13. `scoped_sync_repair.ScopedRepairError`
14. `host.emit`
15. `host.emit`
16. `host.emit`
17. `host.emit`
18. `path_policy.validate_source_root`
19. `path_policy.PathValidationError`
20. `path_policy.validate_path`

## Touches

- [historical_retirement](../modules/historical_retirement.md)
- [host](../modules/host.md)
- [inventory_cache](../modules/inventory_cache.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [path_policy](../modules/path_policy.md)
- [scoped_sync_repair](../modules/scoped_sync_repair.md)
- [source_retirement](../modules/source_retirement.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._sync_run_options_from_request`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
