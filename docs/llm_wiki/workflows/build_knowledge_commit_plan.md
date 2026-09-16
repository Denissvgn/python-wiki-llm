# build_knowledge_commit_plan

**Entry point:** `knowledge_artifacts.build_knowledge_commit_plan`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md)

> Validate and plan one manifest-last knowledge artifact commit.

The supplied projection bytes must already use their canonical wire
encodings.  The evaluated-envelope hash is derived from the validated
knowledge bundle, rather than accepted as an independent caller claim.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_packs.build_storage`
2. `knowledge_index._model_to_payload`
3. `knowledge_index._validated_index_serialization`
4. `knowledge_packs.build_storage`
5. `knowledge_index._model_to_payload`
6. `knowledge_evidence.sha256_bytes`
7. `knowledge_storage.KnowledgeStorageError`
8. `knowledge_evidence.formatted_json_bytes`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)

## Behavior

Selects the explicitly requested or already adopted format, validates the logical native model and prepares canonical physical artifacts through the appropriate storage owner. Existing immutable files must match their commitments. The plan binds root and companion bytes into a new manifest while preserving authority and rejecting oversized or corrupt inputs before publication.
