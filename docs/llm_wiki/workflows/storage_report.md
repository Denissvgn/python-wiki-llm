# storage_report

**Entry point:** `knowledge_storage_diagnostics.storage_report`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_loader](../modules/knowledge_loader.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage_io._absolute_path`
3. `knowledge_storage_io._absolute_path`
4. `knowledge_storage_io.read_guarded`
5. `knowledge_storage.parse_store_root`
6. `knowledge_storage.canonical_bytes`
7. `knowledge_storage.KnowledgeStorageError`
8. `knowledge_storage_lifecycle.stored_object_paths`
9. `knowledge_storage.KnowledgeStorageError`
10. `knowledge_loader.load_knowledge_state`
11. `knowledge_storage.KnowledgeStorageError`
12. `knowledge_artifacts.validated_artifact_bytes`
13. `knowledge_index._model_to_payload`
14. `knowledge_storage.canonical_bytes`
15. `knowledge_storage.canonical_bytes`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Behavior

Reports artifact and object sizes without mutating the wiki. Full mode audits native records and routing against committed metadata and reports unreachable objects. Optional explicit Git endpoints add local historical-blob inspection; incomplete history cannot produce a successful range check.
