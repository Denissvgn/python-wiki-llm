# commit_sharded

**Entry point:** `knowledge_artifacts._commit_sharded`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_storage_io](../modules/knowledge_storage_io.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `filesystem_guard.ensure_guarded_directory`
3. `knowledge_governance.governance_lock`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)

## Behavior

Uses the shared storage lock and guarded writer for indexed JSON objects and ZIP packs. It verifies prior inputs, writes immutable physical artifacts first, publishes the surface/root and commits the manifest last. Exact bytes are rechecked around publication; an interrupted or moved generation yields a failure rather than a mixed valid snapshot.
