# preflight_team_source_selection

**Entry point:** `team_cmd._preflight_team_source_selection`
**Modules involved:** [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md), [sync_manifest](../modules/sync_manifest.md), [team_cmd](../modules/team_cmd.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.resolve_source_selection`
2. `sync_manifest.SyncManifest.load`
3. `source_selection.validate_persisted_source_selection_identity`
4. `source_snapshot.capture_source_selection_inputs`
5. `source_selection.validate_persisted_source_selection_identity`
6. `source_snapshot.build_source_snapshot`

## Touches

- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [team_cmd](../modules/team_cmd.md)

## Behavior

This workflow starts at `team_cmd._preflight_team_source_selection`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
