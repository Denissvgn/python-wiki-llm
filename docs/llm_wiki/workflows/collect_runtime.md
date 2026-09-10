# collect_runtime

**Entry point:** `documentation_native._collect_runtime`
**Modules involved:** [documentation_native](../modules/documentation_native.md), [extraction_jobs](../modules/extraction_jobs.md), [extraction_service](../modules/extraction_service.md), [infrastructure_inventory](../modules/infrastructure_inventory.md), [inventory_cache](../modules/inventory_cache.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.build_source_snapshot`
2. `extraction_service.get_inventory_result`
3. `extraction_service.InventoryRequest`
4. `inventory_cache.InventoryCacheOptions`
5. `extraction_jobs.ExtractionJobRequest.resolved`
6. `extraction_service.get_docker_inventory`
7. `infrastructure_inventory.get_yaml_infrastructure_inventory`

## Touches

- [documentation_native](../modules/documentation_native.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [inventory_cache](../modules/inventory_cache.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `documentation_native._collect_runtime`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
