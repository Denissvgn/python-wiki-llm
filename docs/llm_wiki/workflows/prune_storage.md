# prune_storage

**Entry point:** `knowledge_storage_lifecycle._prune_storage`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md), [manifest_storage](../modules/manifest_storage.md)

> Remove only valid content-addressed objects unreachable from a full audit.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage_io._absolute_path`
3. `knowledge_artifacts.current_knowledge_format`
4. `knowledge_storage.KnowledgeStorageError`
5. `knowledge_storage.canonical_bytes`
6. `knowledge_storage.digest`
7. `knowledge_storage.canonical_bytes`
8. `knowledge_storage.KnowledgeStorageError`
9. `knowledge_storage.KnowledgeStorageError`
10. `knowledge_storage.KnowledgeStorageError`
11. `knowledge_artifacts.validated_artifact_bytes`
12. `knowledge_artifacts.current_knowledge_format`
13. `knowledge_storage.KnowledgeStoreReader`
14. `knowledge_storage.canonical_bytes`
15. `knowledge_storage.KnowledgeStorageError`
16. `knowledge_storage_io._absolute_path`
17. `knowledge_storage_io.read_guarded`
18. `knowledge_packs.inspect_pack`
19. `knowledge_packs.inspect_index_pages`
20. `knowledge_storage.digest`
21. `knowledge_storage.KnowledgeStorageError`
22. `manifest_storage.validate_catalog`
23. `knowledge_storage.decode_bytes`
24. `knowledge_storage.digest`
25. `knowledge_storage.canonical_bytes`
26. `knowledge_packs.PackedKnowledgeStoreReader`
27. `knowledge_storage.digest`
28. `knowledge_storage.canonical_bytes`
29. `knowledge_storage.canonical_bytes`
30. `knowledge_storage.KnowledgeStorageError`
31. `knowledge_governance.governance_lock`
32. `filesystem_guard.unlink_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [manifest_storage](../modules/manifest_storage.md)

## Behavior

This workflow starts at `knowledge_storage_lifecycle._prune_storage`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
