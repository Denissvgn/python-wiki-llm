# apply_diff

**Entry point:** `sync_cmd._apply_diff`
**Modules involved:** [source_selection](../modules/source_selection.md), [sync_analysis](../modules/sync_analysis.md), [sync_cmd](../modules/sync_cmd.md), [sync_manifest](../modules/sync_manifest.md)

> Regenerate pages for new/changed files, deprecate pages for removed files.

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

This workflow converts a categorized source diff into module and entity page
changes. It resolves collision-stable page maps, builds relationships for the
affected symbols, refreshes new or changed pages and shared generated sections,
records unchanged skips, and deprecates pages whose sources disappeared.
Supported semantic prose is merged back when preservation is enabled, and the
returned `SyncResult` accounts for every write state.
