# regenerate_api_contracts_page

**Entry point:** `sync_runtime._regenerate_api_contracts_page`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [host](../modules/host.md), [io](../modules/io.md), [sync_runtime](../modules/sync_runtime.md)

> Regenerate the canonical mixed API surface while preserving Notes.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `bootstrap_runtime._generate_api_contracts_md`
2. `io.read_md`
3. `host.emit`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [host](../modules/host.md)
- [io](../modules/io.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._regenerate_api_contracts_page`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
