# validate_knowledge_artifacts

**Entry point:** `knowledge_artifacts.validate_knowledge_artifacts`
**Modules involved:** [immutable](../modules/immutable.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_graph](../modules/knowledge_graph.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_reuse](../modules/knowledge_reuse.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [section_ownership](../modules/section_ownership.md), [sync_manifest](../modules/sync_manifest.md)

> Validate canonical projections, cross-artifact parity, and manifest basis.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `immutable.freeze`
2. `knowledge_storage_io.StorageReadSession`
3. `knowledge_storage.KnowledgeStorageError`
4. `knowledge_storage.KnowledgeStorageError`
5. `sync_manifest.SyncManifest.from_payload`
6. `knowledge_storage.KnowledgeStorageError`
7. `knowledge_storage.KnowledgeStoreReader`
8. `immutable.freeze`
9. `knowledge_index._validated_index_serialization`
10. `immutable.freeze`
11. `knowledge_index.validate_knowledge_index`
12. `knowledge_storage.logical_digest`
13. `knowledge_index._model_to_payload`
14. `knowledge_storage.KnowledgeStorageError`
15. `knowledge_evidence.sha256_bytes`
16. `knowledge_graph.typed_graph_from_knowledge_extensions`
17. `section_ownership.validate_section_ownership`
18. `knowledge_reuse.validate_reuse_artifact_parity`
19. `knowledge_governance.governance_hash_from_knowledge`
20. `immutable.freeze`
21. `knowledge_evidence.sha256_bytes`
22. `knowledge_envelope.EvaluatedEnvelope`

## Touches

- [immutable](../modules/immutable.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [section_ownership](../modules/section_ownership.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `knowledge_artifacts.validate_knowledge_artifacts`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
