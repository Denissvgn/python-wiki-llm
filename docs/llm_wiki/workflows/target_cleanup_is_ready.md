# target_cleanup_is_ready

**Entry point:** `upgrade_runtime._target_cleanup_is_ready`
**Modules involved:** [host](../modules/host.md), [services_schema](../modules/services_schema.md), [skills](../modules/skills.md), [upgrade_runtime](../modules/upgrade_runtime.md)

> Revalidate the committed target immediately before source destruction.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `skills.verify_reference_skill`
2. `services_schema.classify_managed_schema_block`
3. `host.emit`

## Touches

- [host](../modules/host.md)
- [services_schema](../modules/services_schema.md)
- [skills](../modules/skills.md)
- [upgrade_runtime](../modules/upgrade_runtime.md)

## Behavior

This workflow starts at `upgrade_runtime._target_cleanup_is_ready`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
