# collect_lint_inputs

**Entry point:** `lint_service._collect_lint_inputs`
**Modules involved:** [extraction_jobs](../modules/extraction_jobs.md), [inventory_cache](../modules/inventory_cache.md), [lint_service](../modules/lint_service.md), [sync_manifest](../modules/sync_manifest.md), [team](../modules/team.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extraction_jobs.ExtractionJobPlan`
2. `extraction_jobs.ExtractionJobRequest`
3. `inventory_cache.InventoryCacheOptions`
4. `sync_manifest.SyncManifest`
5. `team.TeamPolicyContext`

## Touches

- [extraction_jobs](../modules/extraction_jobs.md)
- [inventory_cache](../modules/inventory_cache.md)
- [lint_service](../modules/lint_service.md)
- [sync_manifest](../modules/sync_manifest.md)
- [team](../modules/team.md)

## Behavior

This workflow starts at `lint_service._collect_lint_inputs`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
