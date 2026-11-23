# preview_maintenance_preimages

**Entry point:** `sync_transition_execution.preview_maintenance_preimages`
**Modules involved:** [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [sync_ownership](../modules/sync_ownership.md), [sync_transition_execution](../modules/sync_transition_execution.md), [validation](../modules/validation.md)

> Verify the prior owners' live Markdown before and after simulating their transfer.

*plan* is the application's page transition plan. Each prior page is read
from the live wiki and must match its staged copy; after the preview, every
original is checked again, so a concurrent edit invalidates the preview.
*guarded_pages* are further live pages verified the same way without
supplying a preimage. No file handle is held while the preview runs.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io.StorageReadSession`
2. `sync_ownership.PageTransitionError`
3. `validation.portable_path_key`
4. `sync_ownership.PageTransitionError`
5. `sync_ownership.PageTransitionError`
6. `knowledge_storage.KnowledgeStorageError`
7. `knowledge_storage.KnowledgeStorageError`

## Touches

- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [sync_ownership](../modules/sync_ownership.md)
- [sync_transition_execution](../modules/sync_transition_execution.md)
- [validation](../modules/validation.md)

## Behavior

This workflow starts at `sync_transition_execution.preview_maintenance_preimages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
