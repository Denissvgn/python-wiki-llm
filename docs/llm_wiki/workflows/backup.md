# backup

**Entry point:** `knowledge_storage_lifecycle._backup`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.digest`
2. `knowledge_storage.digest`
3. `knowledge_storage.canonical_bytes`
4. `knowledge_storage.KnowledgeStorageError`
5. `knowledge_storage.KnowledgeStorageError`
6. `knowledge_storage_io.read_guarded`
7. `knowledge_storage.KnowledgeStorageError`
8. `filesystem_guard.ensure_guarded_directory`
9. `filesystem_guard.ensure_guarded_directory`
10. `knowledge_storage_io.read_guarded`
11. `knowledge_storage.KnowledgeStorageError`
12. `filesystem_guard.atomic_write_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Behavior

Builds a bounded recovery catalog binding original/target roots and exact generated file bytes. It accepts an empty destination or the same verified snapshot, creates guarded private directories and refuses conflicting recovery content. Backup remains outside the managed wiki and preserves the previous physical format.
