# storage_report

**Entry point:** `knowledge_storage_diagnostics.storage_report`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_loader](../modules/knowledge_loader.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage_io._absolute_path`
3. `knowledge_storage_io._absolute_path`
4. `knowledge_storage_io.read_guarded`
5. `knowledge_storage.parse_store_root`
6. `knowledge_packs.parse_packed_root`
7. `knowledge_packs.packed_format`
8. `knowledge_storage.canonical_bytes`
9. `knowledge_storage.KnowledgeStorageError`
10. `knowledge_storage_lifecycle.stored_object_paths`
11. `knowledge_storage.KnowledgeStorageError`
12. `knowledge_loader.load_knowledge_state`
13. `knowledge_storage.KnowledgeStorageError`
14. `knowledge_artifacts.validated_artifact_bytes`
15. `knowledge_model._concept_to_payload`
16. `knowledge_model._relationship_to_payload`
17. `knowledge_storage.canonical_bytes`
18. `knowledge_storage.canonical_bytes`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Behavior

Inspect physical sizes and, when requested, validate the complete committed snapshot once. Reuse captured audit statistics and serialize records individually for size summaries. Explicit scoped inspection and streaming storage audit have separate validation boundaries.
