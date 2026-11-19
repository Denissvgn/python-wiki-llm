# load_or_seed_manifest

**Entry point:** `sync_runtime._load_or_seed_manifest`
**Modules involved:** [host](../modules/host.md), [maintenance_protocol](../modules/maintenance_protocol.md), [sync_manifest](../modules/sync_manifest.md), [sync_runtime](../modules/sync_runtime.md), [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `maintenance_protocol.guard_maintenance_owner`
2. `wiki_lifecycle.classify_wiki_lifecycle`
3. `sync_manifest.SyncManifest.load`
4. `wiki_lifecycle.bootstrap_guidance`
5. `wiki_lifecycle.migration_guidance`
6. `host.emit`

## Touches

- [host](../modules/host.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [sync_manifest](../modules/sync_manifest.md)
- [sync_runtime](../modules/sync_runtime.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Behavior

This workflow starts at `sync_runtime._load_or_seed_manifest`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
