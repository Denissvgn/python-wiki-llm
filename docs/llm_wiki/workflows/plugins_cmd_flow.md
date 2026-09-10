# plugins_cmd_flow

**Entry point:** `plugins_cmd.run`
**Modules involved:** [config](../modules/config.md), [plugin_samples](../modules/plugin_samples.md), [plugins](../modules/plugins.md), [plugins_cmd](../modules/plugins_cmd.md), [services_schema](../modules/services_schema.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `plugins.list_plugins`
2. `plugin_samples.list_samples`
3. `plugin_samples.export_sample`
4. `plugins.validate_plugin`
5. `config.validate_path`
6. `plugins.remove_plugin`
7. `services_schema.strip_plugin_skill_blocks`
8. `plugins.validate_plugin`

## Touches

- [config](../modules/config.md)
- [plugin_samples](../modules/plugin_samples.md)
- [plugins](../modules/plugins.md)
- [plugins_cmd](../modules/plugins_cmd.md)
- [services_schema](../modules/services_schema.md)

## Behavior

This workflow starts at `plugins_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
