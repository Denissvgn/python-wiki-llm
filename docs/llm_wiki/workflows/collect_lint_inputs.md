# collect_lint_inputs

**Entry point:** `lint_service._collect_lint_inputs`
**Modules involved:** [common](../modules/common.md), [extraction_service](../modules/extraction_service.md), [infrastructure_inventory](../modules/infrastructure_inventory.md), [lint_service](../modules/lint_service.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `common.normalize_include_tests`
2. `source_snapshot.build_source_snapshot`
3. `extraction_service.get_inventory_result`
4. `source_snapshot.unsupported_source_summary`
5. `extraction_service.get_docker_inventory`
6. `infrastructure_inventory.get_yaml_infrastructure_inventory`

## Touches

- [common](../modules/common.md)
- [extraction_service](../modules/extraction_service.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [lint_service](../modules/lint_service.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `lint_service._collect_lint_inputs`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
