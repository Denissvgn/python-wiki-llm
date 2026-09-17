# restore_pruned_storage

**Entry point:** `knowledge_storage_lifecycle.restore_pruned_storage`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md), [storage_spool](../modules/storage_spool.md)

> Restore cleanup preimages into their recorded generation without overwrites.

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
11. `knowledge_storage_io.StorageReadSession`
12. `storage_spool.ByteSpool`
13. `knowledge_storage.KnowledgeStorageError`
14. `knowledge_storage._hash`
15. `knowledge_storage.KnowledgeStorageError`
16. `knowledge_storage.KnowledgeStorageError`
17. `knowledge_storage_io.read_guarded`
18. `knowledge_storage.digest`
19. `knowledge_storage.KnowledgeStorageError`
20. `knowledge_governance.governance_lock`
21. `knowledge_storage_io._absolute_path`
22. `knowledge_storage_io.read_guarded`
23. `filesystem_guard.ensure_guarded_directory`
24. `filesystem_guard.atomic_write_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [storage_spool](../modules/storage_spool.md)

## Behavior

This workflow starts at `knowledge_storage_lifecycle.restore_pruned_storage`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.

Preview and apply require the recorded wiki identity and both generation hashes. Restoration verifies all backup preimages, then rechecks the generation under the storage lock and before each absent file is written. A changed root or manifest stops restoration and preserves recovery evidence; differing existing files remain untouched. Matching commit headers suffice even when other storage objects are missing.
