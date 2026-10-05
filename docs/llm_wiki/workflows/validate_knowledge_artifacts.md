# validate_knowledge_artifacts

**Entry point:** `knowledge_artifacts.validate_knowledge_artifacts`
**Modules involved:** [immutable](../modules/immutable.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_graph](../modules/knowledge_graph.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_reuse](../modules/knowledge_reuse.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [section_ownership](../modules/section_ownership.md), [sync_manifest](../modules/sync_manifest.md)

> Validate canonical projections, cross-artifact parity, and manifest basis.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `immutable.freeze`
2. `immutable.freeze`
3. `knowledge_storage_io.StorageReadSession`
4. `knowledge_storage_io.StorageReadSession.read`
5. `knowledge_storage_io.StorageReadSession.read`
6. `knowledge_storage_io.StorageReadSession.read`
7. `sync_manifest.SyncManifest.from_payload`
8. `immutable.freeze`
9. `knowledge_storage_io.StorageReadSession.recheck`
10. `knowledge_storage_io.StorageReadSession`
11. `knowledge_storage.KnowledgeStorageError`
12. `knowledge_storage.KnowledgeStorageError`
13. `sync_manifest.SyncManifest.from_payload`
14. `knowledge_storage.KnowledgeStorageError`
15. `immutable.freeze`
16. `knowledge_packs.open_knowledge_store`
17. `immutable.freeze`
18. `knowledge_packs.physical_objects`
19. `immutable.freeze`
20. `knowledge_index._validated_index_serialization`
21. `knowledge_index.validate_knowledge_index`
22. `knowledge_storage.logical_digest`
23. `knowledge_index._model_to_payload`
24. `knowledge_storage.KnowledgeStorageError`
25. `immutable.freeze`
26. `knowledge_evidence.sha256_bytes`
27. `knowledge_graph.typed_graph_from_knowledge_extensions`
28. `section_ownership.validate_section_ownership`
29. `knowledge_reuse.validate_reuse_artifact_parity`
30. `knowledge_governance.governance_hash_from_knowledge`
31. `immutable.freeze`
32. `knowledge_evidence.sha256_bytes`
33. `knowledge_envelope.EvaluatedEnvelope`

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
