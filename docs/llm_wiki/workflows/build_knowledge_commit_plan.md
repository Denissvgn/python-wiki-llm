# build_knowledge_commit_plan

**Entry point:** `knowledge_artifacts.build_knowledge_commit_plan`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [maintenance_protocol](../modules/maintenance_protocol.md), [maintenance_state](../modules/maintenance_state.md), [manifest_storage](../modules/manifest_storage.md)

> Validate and plan one manifest-last knowledge artifact commit.

The supplied projection bytes must already use their canonical wire
encodings.  The evaluated-envelope hash is derived from the validated
knowledge bundle, rather than accepted as an independent caller claim.

``prior`` permits byte/compression reuse, without waiving next-state
validation or live commit checks. An optional ``ByteSpool`` is caller-owned
and must remain open until the plan and commit result are no longer used.
Storage objects are staged synchronously; full-model validation still has
its normal output-memory cost.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `manifest_storage.current_manifest_format`
2. `maintenance_state.validate_maintenance_adoption`
3. `maintenance_protocol.load_adoption_marker`
4. `knowledge_storage.canonical_bytes`
5. `knowledge_storage.digest`
6. `knowledge_index._has_validation_operation`
7. `knowledge_index._validated_index_receipt`
8. `knowledge_packs.build_storage`
9. `knowledge_index._model_to_payload`
10. `knowledge_index._has_validation_operation`
11. `knowledge_index._validated_index_receipt`
12. `knowledge_index._validated_index_serialization`
13. `knowledge_packs.build_storage`
14. `knowledge_index._model_to_payload`
15. `knowledge_evidence.sha256_bytes`
16. `knowledge_storage.KnowledgeStorageError`
17. `manifest_storage.build_manifest_store`
18. `knowledge_storage.KnowledgeStorageError`
19. `knowledge_evidence.formatted_json_bytes`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)

## Behavior

Validate the complete next native generation, preserve adopted storage and manifest formats, and derive the artifact commitments. Compatible prior packs and compressed members can be reused by content identity. Optional spooling bounds retained physical buffers; publication still checks exact preimages and replaces the manifest last.
