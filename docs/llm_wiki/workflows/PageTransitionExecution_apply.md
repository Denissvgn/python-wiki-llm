# PageTransitionExecution_apply

**Entry point:** `sync_transition_execution.PageTransitionExecution.apply`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [protected_artifacts](../modules/protected_artifacts.md), [sync_transition_execution](../modules/sync_transition_execution.md), [sync_transitions](../modules/sync_transitions.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_transitions.PageTransitionError`
2. `knowledge_storage_io.StorageReadSession`
3. `knowledge_storage_io.StorageReadSession.read`
4. `knowledge_storage_io.StorageReadSession.read`
5. `sync_transitions.PageTransitionError`
6. `protected_artifacts.ProtectedArtifactStore`
7. `filesystem_guard.atomic_write_private_bytes`
8. `filesystem_guard.atomic_write_private_bytes`
9. `filesystem_guard.unlink_guarded_bytes`
10. `filesystem_guard.ensure_guarded_directory`
11. `filesystem_guard.atomic_write_guarded_bytes`
12. `sync_transitions.PageTransitionError`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [protected_artifacts](../modules/protected_artifacts.md)
- [sync_transition_execution](../modules/sync_transition_execution.md)
- [sync_transitions](../modules/sync_transitions.md)

## Behavior

This workflow starts at `sync_transition_execution.PageTransitionExecution.apply`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
