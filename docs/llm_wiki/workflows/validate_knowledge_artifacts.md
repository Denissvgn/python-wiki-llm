# validate_knowledge_artifacts

**Entry point:** `knowledge_artifacts.validate_knowledge_artifacts`
**Modules involved:** [immutable](../modules/immutable.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_graph](../modules/knowledge_graph.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_reuse](../modules/knowledge_reuse.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [section_ownership](../modules/section_ownership.md), [sync_manifest](../modules/sync_manifest.md)

> Validate canonical projections, cross-artifact parity, and manifest basis.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_index._require_validation_receipt`
2. `knowledge_index._model_to_payload`
3. `knowledge_index._require_validation_receipt`
4. `immutable.freeze`
5. `immutable.freeze`
6. `knowledge_storage_io.StorageReadSession`
7. `knowledge_storage_io.StorageReadSession.read`
8. `knowledge_storage_io.StorageReadSession.read`
9. `knowledge_storage_io.StorageReadSession.read`
10. `sync_manifest.SyncManifest.from_payload`
11. `immutable.freeze`
12. `knowledge_storage_io.StorageReadSession.recheck`
13. `knowledge_storage_io.StorageReadSession`
14. `knowledge_storage.KnowledgeStorageError`
15. `knowledge_storage.KnowledgeStorageError`
16. `sync_manifest.SyncManifest.from_payload`
17. `knowledge_storage.KnowledgeStorageError`
18. `immutable.freeze`
19. `knowledge_packs.open_knowledge_store`
20. `immutable.freeze`
21. `knowledge_packs.physical_objects`
22. `immutable.freeze`
23. `knowledge_index._validated_index_serialization`
24. `knowledge_storage.logical_digest`
25. `knowledge_storage.logical_digest`
26. `knowledge_index._model_to_payload`
27. `knowledge_storage.KnowledgeStorageError`
28. `knowledge_index.validate_knowledge_index`
29. `knowledge_storage.logical_digest`
30. `knowledge_index._model_to_payload`
31. `knowledge_storage.KnowledgeStorageError`
32. `immutable.freeze`
33. `knowledge_evidence.sha256_bytes`
34. `knowledge_graph.typed_graph_from_knowledge_extensions`
35. `section_ownership.validate_section_ownership`
36. `knowledge_reuse.validate_reuse_artifact_parity`
37. `knowledge_governance.governance_hash_from_knowledge`
38. `knowledge_index._require_validation_receipt`
39. `knowledge_index._require_validation_receipt`
40. `immutable.freeze`
41. `knowledge_evidence.sha256_bytes`
42. `knowledge_envelope.EvaluatedEnvelope`

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
