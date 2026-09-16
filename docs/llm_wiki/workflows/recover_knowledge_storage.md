# recover_knowledge_storage

**Entry point:** `knowledge_storage_lifecycle.recover_knowledge_storage`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md), [sync_manifest](../modules/sync_manifest.md)

> Restore an exact interrupted migration; refuse unrelated newer roots.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage_io._absolute_path`
3. `sync_manifest.SyncManifest.from_payload`
4. `knowledge_artifacts.validate_knowledge_artifacts`
5. `knowledge_storage.KnowledgeStorageError`
6. `knowledge_storage_io.StorageReadSession`
7. `knowledge_storage.digest`
8. `knowledge_storage.KnowledgeStorageError`
9. `knowledge_storage.digest`
10. `knowledge_storage.KnowledgeStorageError`
11. `knowledge_storage.digest`
12. `knowledge_storage.KnowledgeStorageError`
13. `knowledge_artifacts.PlannedArtifactWrite`
14. `knowledge_storage.digest`
15. `knowledge_artifacts.KnowledgeCommitPlan`
16. `knowledge_artifacts._commit_sharded`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

Verifies the saved recovery record and refuses roots outside that migration or changed authored authority. It restores the exact prior artifacts through guarded publication. Restoring a historical large file does not remove an outgoing Git-size violation.
