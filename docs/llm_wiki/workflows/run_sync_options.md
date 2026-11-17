# run_sync_options

**Entry point:** `sync_runtime._run_sync_options`
**Modules involved:** [host](../modules/host.md), [scoped_sync_repair](../modules/scoped_sync_repair.md), [sync_analysis_cache](../modules/sync_analysis_cache.md), [sync_runtime](../modules/sync_runtime.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `scoped_sync_repair.ScopedRepairError`
2. `scoped_sync_repair.ScopedRepairError`
3. `scoped_sync_repair.prepare_boundary`
4. `scoped_sync_repair.ScopedRepairError`
5. `host.emit`
6. `sync_analysis_cache.report_capture`
7. `host.emit`

## Touches

- [host](../modules/host.md)
- [scoped_sync_repair](../modules/scoped_sync_repair.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._run_sync_options`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
