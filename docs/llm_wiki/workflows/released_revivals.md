# released_revivals

**Entry point:** `sync_transitions._released_revivals`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [sync_ownership](../modules/sync_ownership.md), [sync_transitions](../modules/sync_transitions.md), [validation](../modules/validation.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io.StorageReadSession`
2. `validation.portable_path_key`
3. `canonical_json.sha256_digest`
4. `sync_ownership.PageTransitionError`
5. `validation.portable_path_key`
6. `canonical_json.sha256_digest`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [sync_ownership](../modules/sync_ownership.md)
- [sync_transitions](../modules/sync_transitions.md)
- [validation](../modules/validation.md)

## Behavior

This workflow starts at `sync_transitions._released_revivals`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
