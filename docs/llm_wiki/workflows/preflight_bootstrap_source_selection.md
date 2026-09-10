# preflight_bootstrap_source_selection

**Entry point:** `bootstrap_runtime._preflight_bootstrap_source_selection`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [bootstrap_service](../modules/bootstrap_service.md), [source_selection](../modules/source_selection.md), [sync_manifest](../modules/sync_manifest.md)

> Protect private workspace refreshes from configured-to-broad downgrade.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_manifest.SyncManifest.load`
2. `bootstrap_service.BootstrapContractError`
3. `source_selection.resolve_source_selection`
4. `source_selection.validate_persisted_source_selection_identity`
5. `bootstrap_service.BootstrapContractError`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [bootstrap_service](../modules/bootstrap_service.md)
- [source_selection](../modules/source_selection.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `bootstrap_runtime._preflight_bootstrap_source_selection`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
