# validate_knowledge_artifacts

**Entry point:** `knowledge_artifacts.validate_knowledge_artifacts`
**Modules involved:** [immutable](../modules/immutable.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_graph](../modules/knowledge_graph.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_reuse](../modules/knowledge_reuse.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [section_ownership](../modules/section_ownership.md), [sync_manifest](../modules/sync_manifest.md)

> Validate canonical projections, cross-artifact parity, and manifest basis.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `immutable.freeze`
2. `immutable.freeze`
3. `knowledge_storage_io.StorageReadSession`
4. `sync_manifest.SyncManifest.from_payload`
5. `immutable.freeze`
6. `knowledge_storage_io.StorageReadSession`
7. `knowledge_storage.KnowledgeStorageError`
8. `knowledge_storage.KnowledgeStorageError`
9. `sync_manifest.SyncManifest.from_payload`
10. `knowledge_storage.KnowledgeStorageError`
11. `immutable.freeze`
12. `knowledge_packs.open_knowledge_store`
13. `immutable.freeze`
14. `knowledge_packs.physical_objects`
15. `immutable.freeze`
16. `knowledge_index._validated_index_serialization`
17. `knowledge_index.validate_knowledge_index`
18. `knowledge_storage.logical_digest`
19. `knowledge_index._model_to_payload`
20. `knowledge_storage.KnowledgeStorageError`
21. `immutable.freeze`
22. `knowledge_evidence.sha256_bytes`
23. `knowledge_graph.typed_graph_from_knowledge_extensions`
24. `section_ownership.validate_section_ownership`
25. `knowledge_reuse.validate_reuse_artifact_parity`
26. `knowledge_governance.governance_hash_from_knowledge`
27. `immutable.freeze`
28. `knowledge_evidence.sha256_bytes`
29. `knowledge_envelope.EvaluatedEnvelope`

## Touches

- [immutable](../modules/immutable.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [section_ownership](../modules/section_ownership.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `knowledge_artifacts.validate_knowledge_artifacts`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
