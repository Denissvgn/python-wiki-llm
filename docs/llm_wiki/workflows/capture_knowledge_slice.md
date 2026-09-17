# capture_knowledge_slice

**Entry point:** `knowledge_storage_access.capture_knowledge_slice`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_access](../modules/knowledge_storage_access.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [manifest_storage](../modules/manifest_storage.md)

> Capture selected stored observations without enumerating the wiki tree.

The v6 commit header and policy are read completely. Unread catalogs remain
unverified; the receipt never represents a full artifact or a live source
evaluation. The owning request calls ``finish`` before publishing its result.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage.KnowledgeStorageError`
3. `knowledge_storage_io.StorageReadSession`
4. `knowledge_storage.KnowledgeStorageError`
5. `knowledge_storage.KnowledgeStorageError`
6. `knowledge_packs.open_knowledge_store`
7. `manifest_storage.read_manifest_header`
8. `knowledge_model._parse_bundle`
9. `knowledge_storage.KnowledgeStorageError`
10. `knowledge_storage.digest`
11. `knowledge_envelope.EvaluatedEnvelope`
12. `knowledge_storage.KnowledgeStorageError`
13. `knowledge_storage.KnowledgeStorageError`
14. `knowledge_storage.digest`
15. `knowledge_storage.KnowledgeStorageError`
16. `knowledge_storage.KnowledgeStorageError`
17. `knowledge_storage.digest`
18. `knowledge_storage.KnowledgeStorageError`
19. `knowledge_governance.parse_governance_ledger`
20. `knowledge_artifacts._decode_json_object`
21. `knowledge_governance.lifecycle_state_by_uid`
22. `knowledge_storage.KnowledgeStorageError`
23. `knowledge_storage.KnowledgeStorageError`
24. `knowledge_governance.natural_key_for`
25. `knowledge_storage.KnowledgeStorageError`
26. `knowledge_storage.KnowledgeStorageError`
27. `knowledge_storage.KnowledgeStorageError`
28. `knowledge_storage.KnowledgeStorageError`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_access](../modules/knowledge_storage_access.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [manifest_storage](../modules/manifest_storage.md)

## Behavior

Read the knowledge root and committed manifest policy, verify generation commitments, then resolve the requested records and required authority. Manifest v6 leaves unrelated source and page catalogs unread. The caller must run the final guarded recheck before using the selected result.
