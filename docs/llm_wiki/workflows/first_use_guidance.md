# first_use_guidance

**Entry point:** `bootstrap_runtime._first_use_guidance`
**Modules involved:** [bootstrap_recovery](../modules/bootstrap_recovery.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [sync_manifest](../modules/sync_manifest.md), [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `bootstrap_recovery.pending_bootstrap`
2. `wiki_lifecycle.classify_wiki_lifecycle`
3. `wiki_lifecycle.migration_guidance`
4. `wiki_lifecycle.sync_guidance`
5. `sync_manifest.SyncManifest.load`

## Touches

- [bootstrap_recovery](../modules/bootstrap_recovery.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [sync_manifest](../modules/sync_manifest.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Behavior

This workflow starts at `bootstrap_runtime._first_use_guidance`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
