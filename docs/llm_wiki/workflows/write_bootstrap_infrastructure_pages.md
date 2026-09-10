# write_bootstrap_infrastructure_pages

**Entry point:** `bootstrap_runtime._write_bootstrap_infrastructure_pages`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [extraction_service](../modules/extraction_service.md), [infrastructure_inventory](../modules/infrastructure_inventory.md), [infrastructure_sync](../modules/infrastructure_sync.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extraction_service.get_docker_inventory`
2. `infrastructure_inventory.get_yaml_infrastructure_inventory`
3. `infrastructure_sync.build_infrastructure_page_map`
4. `infrastructure_inventory.infrastructure_display_label`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [extraction_service](../modules/extraction_service.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)

## Behavior

This workflow starts at `bootstrap_runtime._write_bootstrap_infrastructure_pages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
