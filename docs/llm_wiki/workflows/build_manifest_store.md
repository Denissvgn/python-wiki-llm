# build_manifest_store

**Entry point:** `manifest_storage.build_manifest_store`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [immutable](../modules/immutable.md), [knowledge_storage](../modules/knowledge_storage.md), [manifest_storage](../modules/manifest_storage.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `canonical_json.canonical_chunks`
3. `knowledge_storage.KnowledgeStorageError`
4. `knowledge_storage.logical_digest`
5. `knowledge_storage.canonical_bytes`
6. `knowledge_storage.KnowledgeStorageError`
7. `immutable.freeze`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [immutable](../modules/immutable.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [manifest_storage](../modules/manifest_storage.md)

## Behavior

This workflow starts at `manifest_storage.build_manifest_store`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
