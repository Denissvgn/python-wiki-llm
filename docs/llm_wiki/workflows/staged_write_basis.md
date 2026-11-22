# staged_write_basis

**Entry point:** `sync_runtime._staged_write_basis`
**Modules involved:** [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_protocol](../modules/maintenance_protocol.md), [storage_spool](../modules/storage_spool.md), [sync_runtime](../modules/sync_runtime.md)

> Give a dry run's staged copy the write basis a writing sync would have.

With maintenance adopted, a writing sync captures the whole wiki before
any write and plans knowledge against those preimages and the bytes it
writes. The staged copy gets the same basis, without recovery data since
the copy is discarded, so a dry run plans exactly as the sync would.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `storage_spool.ByteSpool`
3. `maintenance_protocol._capture_spooled_wiki`
4. `maintenance_protocol.WikiWriteBasis`

## Touches

- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [storage_spool](../modules/storage_spool.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._staged_write_basis`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
