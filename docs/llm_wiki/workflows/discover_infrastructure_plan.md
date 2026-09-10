# discover_infrastructure_plan

**Entry point:** `sync_cmd._discover_infrastructure_plan`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [infrastructure_inventory](../modules/infrastructure_inventory.md), [infrastructure_sync](../modules/infrastructure_sync.md), [sync_cmd](../modules/sync_cmd.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extraction_service.get_docker_inventory`
2. `infrastructure_inventory.get_yaml_infrastructure_inventory`
3. `infrastructure_sync.build_infrastructure_sync_plan`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [sync_cmd](../modules/sync_cmd.md)

## Behavior

This workflow starts at `sync_cmd._discover_infrastructure_plan`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
