# current_coverage

**Entry point:** `metrics.current_coverage`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [documentation_query_builder](../modules/documentation_query_builder.md), [extraction_service](../modules/extraction_service.md), [lint_service](../modules/lint_service.md), [metrics](../modules/metrics.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.resolve_source_selection`
2. `source_snapshot.capture_source_selection_inputs`
3. `documentation_query_builder.validate_live_query_source_selection`
4. `source_snapshot.build_source_snapshot`
5. `extraction_service.get_inventory_result`
6. `extraction_service.InventoryRequest`
7. `documentation_query_builder.validate_live_query_source_selection`
8. `bootstrap_runtime.build_entity_occurrence_page_map`
9. `bootstrap_runtime.build_module_page_map`
10. `lint_service._collect_documented_entities`
11. `lint_service._collect_documented_modules`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [extraction_service](../modules/extraction_service.md)
- [lint_service](../modules/lint_service.md)
- [metrics](../modules/metrics.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `metrics.current_coverage`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
