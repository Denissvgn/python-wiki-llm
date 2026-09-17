# ScopedTaskState_revalidate

**Entry point:** `task_context_v2.ScopedTaskState.revalidate`
**Modules involved:** [change_selection](../modules/change_selection.md), [context_packet](../modules/context_packet.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [task_context_v2](../modules/task_context_v2.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `workflow_profile.WorkflowRequestError`
2. `context_packet._assert_source_unchanged`
3. `change_selection.select_changes`
4. `context_packet.ContextPacketSourceMutationError`
5. `knowledge_storage_io.StorageReadSession`
6. `knowledge_storage.KnowledgeStorageError`
7. `knowledge_storage.KnowledgeStorageError`
8. `knowledge_storage.KnowledgeStorageError`

## Touches

- [change_selection](../modules/change_selection.md)
- [context_packet](../modules/context_packet.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [task_context_v2](../modules/task_context_v2.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

Checks retained source and change-selection observations, then rereads every consumed native file and pack range under the remaining wiki budget. Any content, file identity or ancestor mismatch invalidates reuse. Observed bytes and operations are reported even when validation fails.
