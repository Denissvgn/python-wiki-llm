# sync_wiki

**Entry point:** `api.sync_wiki`
**Modules involved:** [api](../modules/api.md), [host](../modules/host.md), [sync_runtime](../modules/sync_runtime.md), [sync_service](../modules/sync_service.md)

> Incrementally update a managed wiki from its source tree.

Runs the same sync as ``llm-wiki sync`` without its console output.
Source plugins load only when ``trust_source_plugins`` is true. A wiki
that sync cannot update (for example one without a manifest) raises
:class:`WorkspaceStateError`; contradictory options raise
:class:`InvalidRequestError`.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_service.SyncRequest`
2. `host.discarding_output`
3. `sync_runtime.execute_sync`

## Touches

- [api](../modules/api.md)
- [host](../modules/host.md)
- [sync_runtime](../modules/sync_runtime.md)
- [sync_service](../modules/sync_service.md)

## Behavior

This workflow starts at `api.sync_wiki`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
