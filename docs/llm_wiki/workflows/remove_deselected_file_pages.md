# remove_deselected_file_pages

**Entry point:** `sync_cmd._remove_deselected_file_pages`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [maintenance_protocol](../modules/maintenance_protocol.md), [sync_cmd](../modules/sync_cmd.md), [validation](../modules/validation.md)

> Remove generated pages whose still-existing source left the policy set.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `validation.portable_path_key`
2. `maintenance_protocol.unlink_maintenance_page`
3. `bootstrap_runtime._module_name_from_path`
4. `validation.portable_path_key`
5. `maintenance_protocol.unlink_maintenance_page`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [sync_cmd](../modules/sync_cmd.md)
- [validation](../modules/validation.md)

## Behavior

This workflow starts at `sync_cmd._remove_deselected_file_pages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
