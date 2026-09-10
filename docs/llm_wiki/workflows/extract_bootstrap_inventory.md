# extract_bootstrap_inventory

**Entry point:** `bootstrap_runtime._extract_bootstrap_inventory`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [bootstrap_service](../modules/bootstrap_service.md), [extraction_service](../modules/extraction_service.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.build_source_snapshot`
2. `extraction_service.get_inventory_result`
3. `extraction_service.print_inventory_failures`
4. `bootstrap_service.BootstrapExtractionError`
5. `source_snapshot.unsupported_source_summary`
6. `source_snapshot.format_unsupported_source_summary`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [bootstrap_service](../modules/bootstrap_service.md)
- [extraction_service](../modules/extraction_service.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `bootstrap_runtime._extract_bootstrap_inventory`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
