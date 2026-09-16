# storage_report

**Entry point:** `knowledge_storage_diagnostics.storage_report`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_loader](../modules/knowledge_loader.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage_io._absolute_path`
3. `knowledge_storage_io._absolute_path`
4. `knowledge_storage_io.read_guarded`
5. `knowledge_storage.parse_store_root`
6. `knowledge_packs.parse_packed_root`
7. `knowledge_storage.canonical_bytes`
8. `knowledge_storage.KnowledgeStorageError`
9. `knowledge_storage_lifecycle.stored_object_paths`
10. `knowledge_storage.KnowledgeStorageError`
11. `knowledge_loader.load_knowledge_state`
12. `knowledge_storage.KnowledgeStorageError`
13. `knowledge_artifacts.validated_artifact_bytes`
14. `knowledge_index._model_to_payload`
15. `knowledge_storage.canonical_bytes`
16. `knowledge_storage.canonical_bytes`
17. `knowledge_packs.open_knowledge_store`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Behavior

Quick reporting measures canonical artifacts and recognized storage files without claiming a full integrity verdict. Full reporting validates the entire committed snapshot and reports reachable/unreachable storage, logical records, pack/index counts and deduplication. Optional outgoing-history inspection uses explicit local Git endpoints and retains incomplete checks as failures.
