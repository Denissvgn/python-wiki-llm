# discover_infrastructure_plan

**Entry point:** `sync_runtime._discover_infrastructure_plan`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [host](../modules/host.md), [infrastructure_inventory](../modules/infrastructure_inventory.md), [infrastructure_sync](../modules/infrastructure_sync.md), [sync_runtime](../modules/sync_runtime.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extraction_service.get_docker_inventory`
2. `infrastructure_inventory.get_yaml_infrastructure_inventory`
3. `infrastructure_sync.build_infrastructure_sync_plan`
4. `host.emit`
5. `host.emit`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [host](../modules/host.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._discover_infrastructure_plan`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
