# apply_sync_changes

**Entry point:** `sync_cmd._apply_sync_changes`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [infrastructure_sync](../modules/infrastructure_sync.md), [progress](../modules/progress.md), [source_snapshot](../modules/source_snapshot.md), [sync_analysis](../modules/sync_analysis.md), [sync_cmd](../modules/sync_cmd.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `progress.observed_phase`
2. `infrastructure_sync.InfrastructureSyncPlan`
3. `source_snapshot.SourceSnapshot`
4. `sync_manifest.SourceSelectionPruneResult`
5. `sync_manifest.SyncManifest`
6. `sync_analysis.SyncDiff`
7. `extraction_service.InventoryResult`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [progress](../modules/progress.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_analysis](../modules/sync_analysis.md)
- [sync_cmd](../modules/sync_cmd.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This is the public-surface application coordinator. It builds the shared
generated-section context, applies source page changes and selection pruning,
updates or defers infrastructure according to the run mode, and creates or
refreshes requested workflow, flow, dependency, and API surfaces. It then
rebuilds `index.md` from the resulting registry and appends an operation log;
manifest and generated knowledge finalization occur after this workflow
returns.
