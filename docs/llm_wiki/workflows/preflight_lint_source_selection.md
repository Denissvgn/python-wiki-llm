# preflight_lint_source_selection

**Entry point:** `lint_service._preflight_lint_source_selection`
**Modules involved:** [lint_service](../modules/lint_service.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.resolve_source_selection`
2. `source_snapshot.capture_source_selection_inputs`
3. `sync_manifest.SyncManifest.load`
4. `source_selection.validate_persisted_source_selection_identity`

## Touches

- [lint_service](../modules/lint_service.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `lint_service._preflight_lint_source_selection`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
