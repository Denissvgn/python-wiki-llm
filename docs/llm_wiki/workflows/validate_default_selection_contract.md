# validate_default_selection_contract

**Entry point:** `ci_installer._validate_default_selection_contract`
**Modules involved:** [ci_installer](../modules/ci_installer.md), [io](../modules/io.md), [source_selection](../modules/source_selection.md), [sync_manifest](../modules/sync_manifest.md)

> Prove the managed wiki can use default source-selection discovery.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `io.first_unsafe_path_component`
2. `sync_manifest.SyncManifest.load`
3. `source_selection.resolve_source_selection`
4. `source_selection.validate_persisted_source_selection_identity`

## Touches

- [ci_installer](../modules/ci_installer.md)
- [io](../modules/io.md)
- [source_selection](../modules/source_selection.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `ci_installer._validate_default_selection_contract`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
