# recover_knowledge_storage

**Entry point:** `knowledge_storage_lifecycle._recover_knowledge_storage`
**Modules involved:** [io](../modules/io.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md), [maintenance_projection](../modules/maintenance_projection.md), [maintenance_state](../modules/maintenance_state.md), [sync_manifest](../modules/sync_manifest.md)

> Restore an exact interrupted migration; refuse unrelated newer roots.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage_io._absolute_path`
3. `sync_manifest.SyncManifest.from_payload`
4. `knowledge_artifacts.validate_knowledge_artifacts`
5. `knowledge_storage.KnowledgeStorageError`
6. `maintenance_state.validate_maintenance_adoption`
7. `knowledge_storage.decode_bytes`
8. `knowledge_storage.canonical_bytes`
9. `knowledge_storage.digest`
10. `knowledge_storage.KnowledgeStorageError`
11. `maintenance_projection.validate_maintenance_projection`
12. `knowledge_storage.KnowledgeStorageError`
13. `knowledge_storage.KnowledgeStorageError`
14. `knowledge_storage_io.StorageReadSession`
15. `knowledge_storage_io.StorageReadSession.read`
16. `knowledge_storage.digest`
17. `knowledge_storage.KnowledgeStorageError`
18. `knowledge_storage_io.StorageReadSession.read`
19. `knowledge_storage.digest`
20. `knowledge_storage.KnowledgeStorageError`
21. `knowledge_storage.digest`
22. `io.decode_markdown_bytes`
23. `knowledge_storage_io.StorageReadSession.read`
24. `knowledge_storage.KnowledgeStorageError`
25. `knowledge_storage.digest`
26. `knowledge_storage_io.StorageReadSession.read`
27. `knowledge_storage.KnowledgeStorageError`
28. `knowledge_storage_io.StorageReadSession.read`
29. `knowledge_storage.KnowledgeStorageError`
30. `knowledge_storage_io.StorageReadSession.read`
31. `knowledge_artifacts.PlannedArtifactWrite`
32. `knowledge_storage.digest`
33. `knowledge_packs.packed_format`
34. `knowledge_artifacts.KnowledgeCommitPlan`
35. `knowledge_storage_io.StorageReadSession.recheck`
36. `knowledge_artifacts._commit_sharded`

## Touches

- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_state](../modules/maintenance_state.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

Verify recovery metadata, historical artifacts and current authored authority. Refuse a knowledge or manifest root outside the recorded migration, then restore exact historical bytes with the manifest last. Recovery changes no Git history.
