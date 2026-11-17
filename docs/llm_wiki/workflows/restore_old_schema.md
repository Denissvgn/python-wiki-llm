# restore_old_schema

**Entry point:** `upgrade_runtime._restore_old_schema`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [host](../modules/host.md), [services_schema](../modules/services_schema.md), [upgrade_runtime](../modules/upgrade_runtime.md)

> Restore an already-cleaned source schema without overwriting new bytes.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `filesystem_guard.atomic_write_guarded_bytes`
2. `services_schema.ManagedSchemaPathError`
3. `host.emit`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [host](../modules/host.md)
- [services_schema](../modules/services_schema.md)
- [upgrade_runtime](../modules/upgrade_runtime.md)

## Behavior

This workflow starts at `upgrade_runtime._restore_old_schema`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
