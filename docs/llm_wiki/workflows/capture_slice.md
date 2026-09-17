# capture_slice

**Entry point:** `knowledge_storage_access._capture_slice`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_access](../modules/knowledge_storage_access.md), [manifest_storage](../modules/manifest_storage.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage.KnowledgeStorageError`
3. `knowledge_packs.open_knowledge_store`
4. `manifest_storage.read_manifest_header`
5. `knowledge_model._parse_bundle`
6. `knowledge_storage.KnowledgeStorageError`
7. `knowledge_storage.digest`
8. `knowledge_envelope.EvaluatedEnvelope`
9. `knowledge_storage.KnowledgeStorageError`
10. `knowledge_storage.KnowledgeStorageError`
11. `knowledge_storage.KnowledgeStorageError`
12. `knowledge_storage.digest`
13. `knowledge_storage.KnowledgeStorageError`
14. `knowledge_storage.KnowledgeStorageError`
15. `knowledge_storage.digest`
16. `knowledge_storage.KnowledgeStorageError`
17. `knowledge_governance.parse_governance_ledger`
18. `knowledge_artifacts._decode_json_object`
19. `knowledge_governance.lifecycle_state_by_uid`
20. `knowledge_storage.KnowledgeStorageError`
21. `knowledge_storage.KnowledgeStorageError`
22. `knowledge_governance.natural_key_for`
23. `knowledge_storage.KnowledgeStorageError`
24. `knowledge_storage.KnowledgeStorageError`
25. `knowledge_storage.KnowledgeStorageError`
26. `knowledge_storage.KnowledgeStorageError`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_access](../modules/knowledge_storage_access.md)
- [manifest_storage](../modules/manifest_storage.md)

## Behavior

This workflow starts at `knowledge_storage_access._capture_slice`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
