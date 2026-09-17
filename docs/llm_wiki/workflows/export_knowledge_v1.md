# export_knowledge_v1

**Entry point:** `knowledge_storage_lifecycle.export_knowledge_v1`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_index.serialize_knowledge_index`
2. `knowledge_storage.KnowledgeStorageError`
3. `knowledge_storage_io._absolute_path`
4. `knowledge_storage_io._absolute_path`
5. `knowledge_storage.KnowledgeStorageError`
6. `knowledge_storage.KnowledgeStorageError`
7. `filesystem_guard.ensure_guarded_directory`
8. `filesystem_guard.atomic_write_guarded_bytes`
9. `knowledge_storage.digest`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Behavior

Reconstructs and validates the complete logical v1 representation, checks its file-size policy and writes only to a new explicit destination outside the managed wiki. It does not downgrade the active store or emit truncated compatibility data.
