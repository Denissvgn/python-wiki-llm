# deprecate_existing_page

**Entry point:** `sync_runtime._deprecate_existing_page`
**Modules involved:** [host](../modules/host.md), [io](../modules/io.md), [sync_runtime](../modules/sync_runtime.md), [validation](../modules/validation.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `validation.portable_path_key`
2. `host.emit`
3. `io.read_md`
4. `host.emit`

## Touches

- [host](../modules/host.md)
- [io](../modules/io.md)
- [sync_runtime](../modules/sync_runtime.md)
- [validation](../modules/validation.md)

## Behavior

This workflow starts at `sync_runtime._deprecate_existing_page`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
