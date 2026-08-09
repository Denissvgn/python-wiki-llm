# print_dry_run_plan

**Entry point:** `sync_cmd._print_dry_run_plan`
**Modules involved:** [infrastructure_sync](../modules/infrastructure_sync.md), [sync_analysis](../modules/sync_analysis.md), [sync_cmd](../modules/sync_cmd.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `infrastructure_sync.InfrastructureSyncPlan`
2. `sync_manifest.SourceSelectionPruneResult`
3. `sync_manifest.SyncManifest`
4. `sync_analysis.SyncDiff`

## Touches

- [infrastructure_sync](../modules/infrastructure_sync.md)
- [sync_analysis](../modules/sync_analysis.md)
- [sync_cmd](../modules/sync_cmd.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

Prints the complete proposed sync without applying it. The plan distinguishes
ordinary from deferred source and infrastructure changes, selection pruning,
generated-surface retirement, flow categories, workflow and dependency
creation, API authority, manifest seeding or repair, runtime refresh, and the
expected artifact actions. It is a reporting boundary only and performs no
wiki writes.
