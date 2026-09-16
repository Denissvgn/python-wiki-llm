# capture_knowledge_slice

**Entry point:** `knowledge_storage_access.capture_knowledge_slice`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_access](../modules/knowledge_storage_access.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [sync_manifest](../modules/sync_manifest.md)

> Capture selected stored observations without enumerating the wiki tree.

The manifest is read completely. Unread surface/record shards remain
unverified; the receipt never represents a full artifact or a live source
evaluation. The owning request calls ``finish`` before publishing its result.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage.KnowledgeStorageError`
3. `knowledge_storage_io.StorageReadSession`
4. `knowledge_storage.KnowledgeStorageError`
5. `knowledge_storage.KnowledgeStorageError`
6. `knowledge_storage.KnowledgeStoreReader`
7. `sync_manifest.SyncManifest.from_payload`
8. `knowledge_artifacts._decode_json_object`
9. `knowledge_model._parse_bundle`
10. `knowledge_storage.KnowledgeStorageError`
11. `knowledge_storage.digest`
12. `knowledge_envelope.EvaluatedEnvelope`
13. `knowledge_storage.KnowledgeStorageError`
14. `knowledge_storage.KnowledgeStorageError`
15. `knowledge_storage.digest`
16. `knowledge_storage.KnowledgeStorageError`
17. `knowledge_storage.KnowledgeStorageError`
18. `knowledge_storage.digest`
19. `knowledge_storage.KnowledgeStorageError`
20. `knowledge_governance.parse_governance_ledger`
21. `knowledge_artifacts._decode_json_object`
22. `knowledge_governance.lifecycle_state_by_uid`
23. `knowledge_storage.KnowledgeStorageError`
24. `knowledge_storage.KnowledgeStorageError`
25. `knowledge_governance.natural_key_for`
26. `knowledge_storage.KnowledgeStorageError`
27. `knowledge_storage.KnowledgeStorageError`
28. `knowledge_storage.KnowledgeStorageError`
29. `knowledge_storage.KnowledgeStorageError`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_access](../modules/knowledge_storage_access.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

Reads a bounded root and commit manifest, follows the required routing and verifies selected records and supporting pages. Optional graph expansion remains bounded. When governance is present, selected identities and lifecycle must agree with the authoritative ledger. The owner finishes a final reread before publishing.
