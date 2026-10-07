# capture_discovery

**Entry point:** `search_discovery_capture.capture_discovery`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_access](../modules/knowledge_storage_access.md), [maintenance_protocol](../modules/maintenance_protocol.md), [maintenance_status](../modules/maintenance_status.md), [search_discovery_capture](../modules/search_discovery_capture.md), [search_source](../modules/search_source.md)

> Read one adopted owner and one selected native concepts/sections slice.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `search_source.captured_manifest`
2. `maintenance_protocol.MaintenanceProtocolError`
3. `maintenance_protocol.guard_maintenance_owner`
4. `knowledge_storage.KnowledgeStorageError`
5. `knowledge_storage.KnowledgeStorageError`
6. `knowledge_storage.canonical_bytes`
7. `knowledge_storage.KnowledgeStorageError`
8. `maintenance_status.build_maintenance_status`
9. `knowledge_storage.KnowledgeStorageError`
10. `knowledge_storage.digest`
11. `knowledge_storage.KnowledgeStorageError`
12. `knowledge_artifacts._decode_json_object`
13. `knowledge_model.parse_knowledge_index`
14. `knowledge_storage.KnowledgeStorageError`
15. `knowledge_storage.KnowledgeStorageError`
16. `knowledge_storage.KnowledgeStorageError`
17. `knowledge_storage_access.capture_knowledge_slice`
18. `knowledge_storage.KnowledgeStorageError`
19. `knowledge_storage.KnowledgeStorageError`
20. `knowledge_storage.digest`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_access](../modules/knowledge_storage_access.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_status](../modules/maintenance_status.md)
- [search_discovery_capture](../modules/search_discovery_capture.md)
- [search_source](../modules/search_source.md)

## Behavior

This workflow starts at `search_discovery_capture.capture_discovery`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
