# captured_adoption_marker

**Entry point:** `knowledge_storage_access._captured_adoption_marker`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_access](../modules/knowledge_storage_access.md), [maintenance_state](../modules/maintenance_state.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `maintenance_state.validate_maintenance_adoption`
2. `knowledge_artifacts._decode_json_object`
3. `knowledge_storage.canonical_bytes`
4. `knowledge_storage.KnowledgeStorageError`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_access](../modules/knowledge_storage_access.md)
- [maintenance_state](../modules/maintenance_state.md)

## Behavior

This workflow starts at `knowledge_storage_access._captured_adoption_marker`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
