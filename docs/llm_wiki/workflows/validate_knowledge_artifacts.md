# validate_knowledge_artifacts

**Entry point:** `knowledge_artifacts.validate_knowledge_artifacts`
**Modules involved:** [immutable](../modules/immutable.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [sync_manifest](../modules/sync_manifest.md)

> Validate canonical projections, cross-artifact parity, and manifest basis.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_index._validator_identity`
2. `knowledge_index._require_validation_receipt`
3. `knowledge_index._model_to_payload`
4. `knowledge_index._require_validation_receipt`
5. `immutable.freeze`
6. `immutable.freeze`
7. `knowledge_storage_io.StorageReadSession`
8. `knowledge_storage_io.StorageReadSession.read`
9. `knowledge_storage_io.StorageReadSession.read`
10. `knowledge_storage_io.StorageReadSession.read`
11. `sync_manifest.SyncManifest.from_payload`
12. `immutable.freeze`
13. `knowledge_storage_io.StorageReadSession.recheck`
14. `knowledge_storage_io.StorageReadSession`
15. `knowledge_storage.KnowledgeStorageError`
16. `knowledge_storage.KnowledgeStorageError`
17. `sync_manifest.SyncManifest.from_payload`
18. `knowledge_storage.KnowledgeStorageError`
19. `immutable.freeze`
20. `knowledge_packs.open_knowledge_store`
21. `immutable.freeze`
22. `knowledge_packs.physical_objects`
23. `immutable.freeze`
24. `immutable.freeze`
25. `knowledge_index._model_to_payload`
26. `knowledge_index._validated_index_data`
27. `knowledge_storage.logical_digest`
28. `knowledge_storage.logical_digest`
29. `knowledge_index._model_to_payload`
30. `knowledge_storage.KnowledgeStorageError`
31. `knowledge_index.validate_knowledge_index`
32. `immutable.freeze`
33. `immutable.freeze`
34. `knowledge_index._model_to_payload`
35. `knowledge_storage.logical_digest`
36. `knowledge_storage.KnowledgeStorageError`

## Touches

- [immutable](../modules/immutable.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `knowledge_artifacts.validate_knowledge_artifacts`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
