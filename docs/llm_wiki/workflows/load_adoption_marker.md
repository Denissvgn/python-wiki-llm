# load_adoption_marker

**Entry point:** `maintenance_protocol.load_adoption_marker`
**Modules involved:** [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_protocol](../modules/maintenance_protocol.md), [maintenance_state](../modules/maintenance_state.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `knowledge_storage_io.read_guarded`
3. `maintenance_state.validate_maintenance_adoption`
4. `knowledge_storage.canonical_bytes`

## Touches

- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_state](../modules/maintenance_state.md)

## Behavior

This workflow starts at `maintenance_protocol.load_adoption_marker`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
