# build_apply_diff_context

**Entry point:** `sync_cmd._build_apply_diff_context`
**Modules involved:** [source_selection](../modules/source_selection.md), [sync_analysis](../modules/sync_analysis.md), [sync_cmd](../modules/sync_cmd.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.SourceSelectionPolicy`
2. `sync_manifest.SyncManifest`
3. `sync_analysis.SyncDiff`

## Touches

- [source_selection](../modules/source_selection.md)
- [sync_analysis](../modules/sync_analysis.md)
- [sync_cmd](../modules/sync_cmd.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

Builds the immutable context used while applying one diff. The context binds
the validated inventory and manifest to collision-stable module/entity maps,
current page sets, generated relationship data, metadata-only paths, semantic
preservation policy, and the resolved source-selection policy. Downstream page
writers therefore share one consistent view rather than recalculating names or
ownership independently.
