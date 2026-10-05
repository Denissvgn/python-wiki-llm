# build_manifest_store

**Entry point:** `manifest_storage.build_manifest_store`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [immutable](../modules/immutable.md), [knowledge_storage](../modules/knowledge_storage.md), [manifest_storage](../modules/manifest_storage.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `sync_manifest.SyncManifest.from_payload`
3. `canonical_json.canonical_chunks`
4. `knowledge_storage.KnowledgeStorageError`
5. `knowledge_storage.logical_digest`
6. `knowledge_storage.canonical_bytes`
7. `knowledge_storage.KnowledgeStorageError`
8. `immutable.freeze`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [immutable](../modules/immutable.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [manifest_storage](../modules/manifest_storage.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `manifest_storage.build_manifest_store`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
