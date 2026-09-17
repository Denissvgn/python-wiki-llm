# prune_backup

**Entry point:** `knowledge_storage_lifecycle._prune_backup`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `filesystem_guard.ensure_guarded_directory`
2. `knowledge_storage.KnowledgeStorageError`
3. `filesystem_guard.ensure_guarded_directory`
4. `filesystem_guard.atomic_write_guarded_bytes`
5. `knowledge_storage_io.read_guarded`
6. `knowledge_storage.KnowledgeStorageError`
7. `knowledge_storage.canonical_bytes`
8. `filesystem_guard.atomic_write_guarded_bytes`
9. `knowledge_storage_io.read_guarded`
10. `knowledge_storage.KnowledgeStorageError`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Behavior

This workflow starts at `knowledge_storage_lifecycle._prune_backup`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
