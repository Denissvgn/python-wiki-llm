# exit_if_large_unforced_diff

**Entry point:** `sync_cmd._exit_if_large_unforced_diff`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [infrastructure_sync](../modules/infrastructure_sync.md), [sync_analysis](../modules/sync_analysis.md), [sync_cmd](../modules/sync_cmd.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `infrastructure_sync.InfrastructureSyncPlan`
2. `sync_manifest.SyncManifest`
3. `sync_analysis.SyncDiff`
4. `extraction_service.InventoryResult`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [sync_analysis](../modules/sync_analysis.md)
- [sync_cmd](../modules/sync_cmd.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

Evaluates source-page and, when applicable, infrastructure removals against the
current manifest before writes begin. A normal-sized change returns silently.
An unusually broad unforced change prints the reason, recommends an explicit
review before `--force`, emits requested cache diagnostics, and exits without
modifying the wiki.
