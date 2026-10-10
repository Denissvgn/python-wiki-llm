# export_knowledge_v1

**Entry point:** `knowledge_storage_lifecycle.export_knowledge_v1`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_index.serialize_knowledge_index`
3. `knowledge_storage.KnowledgeStorageError`
4. `knowledge_storage_io._absolute_path`
5. `knowledge_storage_io._absolute_path`
6. `knowledge_storage.KnowledgeStorageError`
7. `knowledge_storage.KnowledgeStorageError`
8. `filesystem_guard.ensure_guarded_directory`
9. `filesystem_guard.atomic_write_guarded_bytes`
10. `knowledge_storage.digest`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Behavior

For a legacy owner, reconstructs and validates the complete logical v1 representation, checks its file-size policy and writes only to a new explicit destination outside the managed wiki. Adopted ordinary-maintenance authority refuses standalone v1 export before writing because that representation would omit its owner and history. Complete matching authority bundles remain the recovery route. Export never downgrades the active store or emits truncated compatibility data.
