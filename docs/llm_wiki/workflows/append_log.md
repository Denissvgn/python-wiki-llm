# append_log

**Entry point:** `sync_cmd._append_log`
**Modules involved:** [infrastructure_sync](../modules/infrastructure_sync.md), [source_snapshot](../modules/source_snapshot.md), [sync_analysis](../modules/sync_analysis.md), [sync_cmd](../modules/sync_cmd.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `infrastructure_sync.InfrastructureSyncPlan`
2. `source_snapshot.SourceSnapshot`
3. `sync_manifest.SourceSelectionPruneResult`
4. `sync_analysis.SyncDiff`

## Touches

- [infrastructure_sync](../modules/infrastructure_sync.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_analysis](../modules/sync_analysis.md)
- [sync_cmd](../modules/sync_cmd.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

After page and index updates, this workflow appends one dated operation record
to `log.md`, creating the log header when the file is absent. It records a
portable source label, source-selection and producer details, page counters,
semantic preservation, and only the source, infrastructure, surface, move, or
retirement actions that were actually applied. Deferred work is counted as
deferred rather than reported as completed.
