# finalize_bootstrap_artifacts

**Entry point:** `bootstrap_runtime._finalize_bootstrap_artifacts`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [extraction_service](../modules/extraction_service.md), [io](../modules/io.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `io.io`
2. `knowledge_artifacts.KnowledgeCommitResult`
3. `sync_manifest.SyncManifest`
4. `extraction_service.InventoryResult`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [extraction_service](../modules/extraction_service.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

Evaluates the completed Markdown tree into a canonical surface index, combines
it with the exact source snapshot, page maps, repository identity, generation
options, plugin producers, and graph observations, then calls the shared
runtime finalizer. The finalizer commits a mutually consistent surface index,
knowledge index, envelope, and sync manifest. Each artifact write is folded
back into bootstrap's created, updated, or skipped accounting.
