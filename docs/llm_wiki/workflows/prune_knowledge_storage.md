# prune_knowledge_storage

**Entry point:** `knowledge_storage_lifecycle.prune_knowledge_storage`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md), [manifest_storage](../modules/manifest_storage.md)

> Remove only valid content-addressed objects unreachable from a full audit.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage_io._absolute_path`
3. `knowledge_artifacts.current_knowledge_format`
4. `knowledge_storage.KnowledgeStorageError`
5. `knowledge_artifacts.validated_artifact_bytes`
6. `knowledge_artifacts.current_knowledge_format`
7. `knowledge_storage.KnowledgeStoreReader`
8. `knowledge_storage.canonical_bytes`
9. `knowledge_storage_io.read_guarded`
10. `knowledge_packs.inspect_pack`
11. `knowledge_storage.digest`
12. `knowledge_storage.KnowledgeStorageError`
13. `manifest_storage.validate_catalog`
14. `knowledge_storage.decode_bytes`
15. `knowledge_storage.digest`
16. `knowledge_storage.canonical_bytes`
17. `knowledge_packs.PackedKnowledgeStoreReader`
18. `knowledge_storage.digest`
19. `knowledge_governance.governance_lock`
20. `filesystem_guard.unlink_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [manifest_storage](../modules/manifest_storage.md)

## Behavior

Validate the committed indexed generation and enumerate owned knowledge and manifest object namespaces. Retain unknown or malformed entries. Applying the preview rechecks current authority and each deletion preimage before removing recognized unreachable files.
