# deprecate_removed_files

**Entry point:** `sync_cmd._deprecate_removed_files`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [source_selection](../modules/source_selection.md), [sync_cmd](../modules/sync_cmd.md), [validation](../modules/validation.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.path_is_selected`
2. `bootstrap_runtime._module_name_from_path`
3. `validation.portable_path_key`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [source_selection](../modules/source_selection.md)
- [sync_cmd](../modules/sync_cmd.md)
- [validation](../modules/validation.md)

## Behavior

This workflow starts at `sync_cmd._deprecate_removed_files`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
