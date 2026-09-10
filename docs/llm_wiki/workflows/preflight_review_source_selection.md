# preflight_review_source_selection

**Entry point:** `review_cmd._preflight_review_source_selection`
**Modules involved:** [review_cmd](../modules/review_cmd.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.resolve_source_selection`
2. `sync_manifest.SyncManifest.load`
3. `source_snapshot.capture_source_selection_inputs`
4. `source_selection.validate_persisted_source_selection_identity`
5. `source_snapshot.build_source_snapshot`

## Touches

- [review_cmd](../modules/review_cmd.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `review_cmd._preflight_review_source_selection`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
