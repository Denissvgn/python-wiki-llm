# storage_report

**Entry point:** `knowledge_storage_diagnostics._storage_report`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_loader](../modules/knowledge_loader.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

> Inspect within existing bounds; the caller retains storage-limit gaps.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `knowledge_storage_io.read_guarded`
3. `knowledge_storage.parse_store_root`
4. `knowledge_packs.parse_packed_root`
5. `knowledge_packs.packed_format`
6. `knowledge_storage.canonical_bytes`
7. `knowledge_storage.KnowledgeStorageError`
8. `knowledge_storage_lifecycle.stored_object_paths`
9. `knowledge_storage.KnowledgeStorageError`
10. `knowledge_loader.load_knowledge_state`
11. `knowledge_storage.KnowledgeStorageError`
12. `knowledge_artifacts.validated_artifact_bytes`
13. `knowledge_model._concept_to_payload`
14. `knowledge_model._relationship_to_payload`
15. `knowledge_storage.canonical_bytes`
16. `knowledge_storage.canonical_bytes`

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


Retention fields distinguish complete namespace and size inspection from validated active references and unvalidated unreferenced candidates. When an existing storage limit interrupts inspection, return failure with the observed prefix and an explicit dry-run prune-storage route; do not run a replacement audit, read orphan payloads, prune files or increase limits. Preview and explicit generation-bound apply remain separate operations with verified recovery preimages.
