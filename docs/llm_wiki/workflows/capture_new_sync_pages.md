# capture_new_sync_pages

**Entry point:** `sync_recovery.capture_new_sync_pages`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [host](../modules/host.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [sync_recovery](../modules/sync_recovery.md)

> Retain rejected writes; never repair them implicitly.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `canonical_json.sha256_digest`
3. `knowledge_storage.canonical_bytes`
4. `host.emit`
5. `host.emit`
6. `host.emit`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [host](../modules/host.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [sync_recovery](../modules/sync_recovery.md)

## Behavior

This workflow starts at `sync_recovery.capture_new_sync_pages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
