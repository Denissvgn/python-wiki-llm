# read_manifest_header

**Entry point:** `manifest_storage.read_manifest_header`
**Modules involved:** [immutable](../modules/immutable.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_storage](../modules/knowledge_storage.md), [manifest_storage](../modules/manifest_storage.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_artifacts._decode_json_object`
2. `sync_manifest.SyncManifest.from_payload`
3. `immutable.freeze`
4. `knowledge_storage.canonical_bytes`
5. `knowledge_storage.KnowledgeStorageError`
6. `sync_manifest.validate_manifest_policy`
7. `sync_manifest.ManifestArtifactHashes.from_payload`
8. `immutable.freeze`

## Touches

- [immutable](../modules/immutable.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [manifest_storage](../modules/manifest_storage.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `manifest_storage.read_manifest_header`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
