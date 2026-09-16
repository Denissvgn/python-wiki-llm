# build_knowledge_commit_plan

**Entry point:** `knowledge_artifacts.build_knowledge_commit_plan`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_storage](../modules/knowledge_storage.md)

> Validate and plan one manifest-last knowledge artifact commit.

The supplied projection bytes must already use their canonical wire
encodings.  The evaluated-envelope hash is derived from the validated
knowledge bundle, rather than accepted as an independent caller claim.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.build_knowledge_store`
2. `knowledge_index._model_to_payload`
3. `knowledge_index._validated_index_serialization`
4. `knowledge_storage.build_knowledge_store`
5. `knowledge_index._model_to_payload`
6. `knowledge_evidence.sha256_bytes`
7. `knowledge_storage.KnowledgeStorageError`
8. `knowledge_evidence.formatted_json_bytes`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_storage](../modules/knowledge_storage.md)

## Behavior

Validates the logical snapshot, preserves an adopted storage format and prepares exact-byte artifact actions. V2 models are encoded directly into bounded objects without allocating a v1 monolith. Unknown formats, corrupt immutable objects and file-size policy failures stop planning before publication.
