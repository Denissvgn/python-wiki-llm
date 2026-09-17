# restore_pruned_storage

**Entry point:** `knowledge_storage_lifecycle.restore_pruned_storage`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md), [storage_spool](../modules/storage_spool.md)

> Restore verified cleanup preimages without overwriting differing files.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `knowledge_storage_io._absolute_path`
3. `knowledge_storage.decode_bytes`
4. `knowledge_storage_io.read_guarded`
5. `knowledge_storage.digest`
6. `knowledge_storage.canonical_bytes`
7. `knowledge_storage.digest`
8. `knowledge_storage.KnowledgeStorageError`
9. `knowledge_storage._hash`
10. `knowledge_storage._hash`
11. `storage_spool.ByteSpool`
12. `knowledge_storage.KnowledgeStorageError`
13. `knowledge_storage._hash`
14. `knowledge_storage.KnowledgeStorageError`
15. `knowledge_storage.KnowledgeStorageError`
16. `knowledge_storage_io.read_guarded`
17. `knowledge_storage.digest`
18. `knowledge_storage.KnowledgeStorageError`
19. `knowledge_governance.governance_lock`
20. `knowledge_storage_io._absolute_path`
21. `knowledge_storage_io.read_guarded`
22. `filesystem_guard.ensure_guarded_directory`
23. `filesystem_guard.atomic_write_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [storage_spool](../modules/storage_spool.md)

## Behavior

This workflow starts at `knowledge_storage_lifecycle.restore_pruned_storage`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
