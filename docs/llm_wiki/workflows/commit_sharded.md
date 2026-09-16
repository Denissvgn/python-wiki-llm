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

Acquires the storage mutation lock, verifies the planned previous artifacts, writes immutable objects and verifies them, then publishes the root and sync manifest in order. An interruption may leave unreferenced objects; it cannot make a mixed generation pass validation.
