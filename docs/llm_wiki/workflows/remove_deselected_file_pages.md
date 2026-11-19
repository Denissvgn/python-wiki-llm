# remove_deselected_file_pages

**Entry point:** `sync_runtime._remove_deselected_file_pages`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [host](../modules/host.md), [maintenance_protocol](../modules/maintenance_protocol.md), [sync_runtime](../modules/sync_runtime.md), [validation](../modules/validation.md)

> Remove generated pages whose still-existing source left the policy set.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `validation.portable_path_key`
2. `maintenance_protocol.unlink_maintenance_page`
3. `host.emit`
4. `bootstrap_runtime._module_name_from_path`
5. `validation.portable_path_key`
6. `maintenance_protocol.unlink_maintenance_page`
7. `host.emit`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [host](../modules/host.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [sync_runtime](../modules/sync_runtime.md)
- [validation](../modules/validation.md)

## Behavior

This workflow starts at `sync_runtime._remove_deselected_file_pages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
