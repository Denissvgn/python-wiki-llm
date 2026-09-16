# prune_knowledge_storage

**Entry point:** `knowledge_storage_lifecycle.prune_knowledge_storage`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

> Remove only valid content-addressed objects unreachable from a full audit.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage_io._absolute_path`
3. `knowledge_artifacts.current_knowledge_format`
4. `knowledge_storage.KnowledgeStorageError`
5. `knowledge_artifacts.validated_artifact_bytes`
6. `knowledge_storage.KnowledgeStoreReader`
7. `knowledge_storage_io.read_guarded`
8. `knowledge_storage.digest`
9. `knowledge_storage.KnowledgeStorageError`
10. `knowledge_storage.decode_bytes`
11. `knowledge_storage.digest`
12. `knowledge_governance.governance_lock`
13. `filesystem_guard.unlink_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Behavior

Audits the current generation before determining reachability. Only recognized checksum-valid objects outside the reachable set are eligible for explicit removal. The preview lists actions; live, unknown and busy files remain protected.
