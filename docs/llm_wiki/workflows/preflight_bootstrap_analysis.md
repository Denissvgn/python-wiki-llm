# preflight_bootstrap_analysis

**Entry point:** `bootstrap_runtime._preflight_bootstrap_analysis`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [bootstrap_service](../modules/bootstrap_service.md), [extraction_service](../modules/extraction_service.md), [helper_runtime](../modules/helper_runtime.md), [source_snapshot](../modules/source_snapshot.md)

> Validate and ready selected helpers under locks, before journal creation.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `bootstrap_service.BootstrapContractError`
2. `helper_runtime.current_helper_operation`
3. `source_snapshot.build_source_snapshot`
4. `extraction_service.prepare_inventory_helpers`
5. `extraction_service.InventoryRequest`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [bootstrap_service](../modules/bootstrap_service.md)
- [extraction_service](../modules/extraction_service.md)
- [helper_runtime](../modules/helper_runtime.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `bootstrap_runtime._preflight_bootstrap_analysis`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
