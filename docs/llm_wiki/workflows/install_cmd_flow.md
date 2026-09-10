# install_cmd_flow

**Entry point:** `install_cmd.run`
**Modules involved:** [config](../modules/config.md), [install_cmd](../modules/install_cmd.md), [plugins](../modules/plugins.md), [services_schema](../modules/services_schema.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_path`
2. `plugins.install_plugin`
3. `config.read_config`
4. `services_schema.refresh_skill_blocks`

## Touches

- [config](../modules/config.md)
- [install_cmd](../modules/install_cmd.md)
- [plugins](../modules/plugins.md)
- [services_schema](../modules/services_schema.md)

## Behavior

This workflow starts at `install_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
