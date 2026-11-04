# hash_addressed_storage

**Entry point:** `maintenance_protocol._hash_addressed_storage`
**Modules involved:** [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [maintenance_protocol](../modules/maintenance_protocol.md), [manifest_storage](../modules/manifest_storage.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.digest`
2. `knowledge_storage.object_path`
3. `manifest_storage.object_path`
4. `knowledge_packs.index_path`
5. `knowledge_packs.index_page_path`

## Touches

- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [manifest_storage](../modules/manifest_storage.md)

## Behavior

This workflow starts at `maintenance_protocol._hash_addressed_storage`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
