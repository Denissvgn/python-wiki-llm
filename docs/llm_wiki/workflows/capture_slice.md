# capture_slice

**Entry point:** `knowledge_storage_access._capture_slice`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [concept_identity](../modules/concept_identity.md), [integrations](../modules/integrations.md), [io](../modules/io.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_access](../modules/knowledge_storage_access.md), [maintenance_projection](../modules/maintenance_projection.md), [manifest_storage](../modules/manifest_storage.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_model.parse_knowledge_index`
3. `knowledge_artifacts._decode_json_object`
4. `knowledge_storage.KnowledgeStorageError`
5. `knowledge_packs.open_knowledge_store`
6. `manifest_storage.read_manifest_header`
7. `knowledge_model._parse_bundle`
8. `knowledge_storage.KnowledgeStorageError`
9. `canonical_json.sha256_digest`
10. `knowledge_envelope.EvaluatedEnvelope`
11. `knowledge_storage.KnowledgeStorageError`
12. `knowledge_storage.KnowledgeStorageError`
13. `canonical_json.sha256_digest`
14. `knowledge_storage.canonical_bytes`
15. `knowledge_storage.KnowledgeStorageError`
16. `knowledge_storage.KnowledgeStorageError`
17. `maintenance_projection.validate_maintenance_binding`
18. `knowledge_storage.KnowledgeStorageError`
19. `knowledge_storage.KnowledgeStorageError`
20. `knowledge_storage.KnowledgeStorageError`
21. `knowledge_storage._selected_collections`
22. `knowledge_storage.KnowledgeStorageError`
23. `knowledge_storage.KnowledgeSlice`
24. `knowledge_storage.canonical_bytes`
25. `integrations.attributes`
26. `knowledge_storage.KnowledgeStorageError`
27. `knowledge_artifacts._decode_json_object`
28. `manifest_storage.ManifestStoreReader`
29. `manifest_storage.ManifestStoreReader.field`
30. `manifest_storage.ManifestStoreReader.field`
31. `knowledge_storage.KnowledgeStorageError`
32. `knowledge_storage.KnowledgeStorageError`
33. `canonical_json.sha256_digest`
34. `io.decode_markdown_bytes`
35. `knowledge_storage.KnowledgeStorageError`
36. `io.decode_markdown_bytes`
37. `knowledge_storage.KnowledgeStorageError`
38. `knowledge_storage.KnowledgeStorageError`
39. `knowledge_artifacts._decode_json_object`
40. `knowledge_storage.KnowledgeStorageError`
41. `maintenance_projection.validate_maintenance_projection`
42. `knowledge_storage.KnowledgeStorageError`
43. `knowledge_storage.KnowledgeStorageError`
44. `canonical_json.sha256_digest`
45. `knowledge_storage.KnowledgeStorageError`
46. `knowledge_governance.parse_governance_ledger`
47. `knowledge_artifacts._decode_json_object`
48. `knowledge_governance.lifecycle_state_by_uid`
49. `knowledge_storage.KnowledgeStorageError`
50. `knowledge_storage.KnowledgeStorageError`
51. `concept_identity.natural_key_for`
52. `knowledge_storage.KnowledgeStorageError`
53. `knowledge_storage.KnowledgeStorageError`
54. `knowledge_governance._validate_selected_supersession_edges`
55. `knowledge_storage.KnowledgeStorageError`
56. `knowledge_storage.KnowledgeStorageError`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [concept_identity](../modules/concept_identity.md)
- [integrations](../modules/integrations.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_access](../modules/knowledge_storage_access.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [manifest_storage](../modules/manifest_storage.md)

## Behavior

This workflow starts at `knowledge_storage_access._capture_slice`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
