# referenced_storage_report

**Entry point:** `knowledge_storage_diagnostics._referenced_storage_report`
**Modules involved:** [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

> Audit a stable generation and namespace without performing cleanup.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io.StorageReadSession`
2. `knowledge_storage_lifecycle.stored_object_paths`
3. `knowledge_storage_lifecycle.stored_object_paths`
4. `knowledge_storage.KnowledgeStorageError`

## Touches

- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Behavior

This workflow starts at `knowledge_storage_diagnostics._referenced_storage_report`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
