# merge_inventory_results

**Entry point:** `extraction_service._merge_inventory_results`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [imports](../modules/imports.md), [packages](../modules/packages.md), [python_contracts](../modules/python_contracts.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `packages.discover_packages`
2. `packages.stamp_inventory_packages`
3. `imports.build_module_path_resolver`
4. `python_contracts.finalize_inventory_model_kinds`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [imports](../modules/imports.md)
- [packages](../modules/packages.md)
- [python_contracts](../modules/python_contracts.md)

## Behavior

This workflow starts at `extraction_service._merge_inventory_results`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
