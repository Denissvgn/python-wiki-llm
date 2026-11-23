# run_sync_options

**Entry point:** `sync_runtime._run_sync_options`
**Modules involved:** [historical_retirement](../modules/historical_retirement.md), [host](../modules/host.md), [scoped_sync_repair](../modules/scoped_sync_repair.md), [sync_analysis_cache](../modules/sync_analysis_cache.md), [sync_runtime](../modules/sync_runtime.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `scoped_sync_repair.ScopedRepairError`
2. `scoped_sync_repair.ScopedRepairError`
3. `scoped_sync_repair.prepare_boundary`
4. `historical_retirement.released_inputs`
5. `scoped_sync_repair.ScopedRepairError`
6. `host.emit`
7. `sync_analysis_cache.report_capture`
8. `host.emit`

## Touches

- [historical_retirement](../modules/historical_retirement.md)
- [host](../modules/host.md)
- [scoped_sync_repair](../modules/scoped_sync_repair.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._run_sync_options`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
