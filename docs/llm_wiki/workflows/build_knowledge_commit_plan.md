# build_knowledge_commit_plan

**Entry point:** `knowledge_artifacts.build_knowledge_commit_plan`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [manifest_storage](../modules/manifest_storage.md)

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
2. `knowledge_packs.build_storage`
3. `knowledge_index._model_to_payload`
4. `knowledge_index._validated_index_serialization`
5. `knowledge_packs.build_storage`
6. `knowledge_index._model_to_payload`
7. `knowledge_evidence.sha256_bytes`
8. `knowledge_storage.KnowledgeStorageError`
9. `manifest_storage.build_manifest_store`
10. `knowledge_storage.KnowledgeStorageError`
11. `knowledge_evidence.formatted_json_bytes`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [manifest_storage](../modules/manifest_storage.md)

## Behavior

Validate the complete next native generation, preserve adopted storage and manifest formats, and derive the artifact commitments. Compatible prior packs and compressed members can be reused by content identity. Optional spooling bounds retained physical buffers; publication still checks exact preimages and replaces the manifest last.
