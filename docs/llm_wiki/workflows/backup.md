# backup

**Entry point:** `knowledge_storage_lifecycle._backup`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.digest`
2. `knowledge_storage.digest`
3. `knowledge_storage.canonical_bytes`
4. `knowledge_storage.KnowledgeStorageError`
5. `knowledge_storage_io.read_guarded`
6. `knowledge_storage.KnowledgeStorageError`
7. `filesystem_guard.ensure_guarded_directory`
8. `filesystem_guard.ensure_guarded_directory`
9. `knowledge_storage_io.read_guarded`
10. `knowledge_storage.KnowledgeStorageError`
11. `filesystem_guard.atomic_write_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Behavior

Creates a verified recovery snapshot outside the managed wiki before migration changes canonical artifacts. Existing recovery content must match exactly; unrelated files are never overwritten. The recovery record binds every retained artifact and the expected migration target.
