# check_data_flow_diagnostics

**Entry point:** `lint_service._check_data_flow_diagnostics`
**Modules involved:** [data_flow](../modules/data_flow.md), [entrypoints](../modules/entrypoints.md), [extraction_service](../modules/extraction_service.md), [flow_followup](../modules/flow_followup.md), [lint_service](../modules/lint_service.md), [plugins](../modules/plugins.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extraction_service.resolve_call_edges`
2. `entrypoints._iter_callables`
3. `entrypoints.get_entry_points`
4. `entrypoints.read_console_scripts`
5. `plugins.runtime_plugin_fallback_root`
6. `data_flow.analyze_data_flow`
7. `entrypoints.build_flow`
8. `flow_followup.validate_request`

## Touches

- [data_flow](../modules/data_flow.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [flow_followup](../modules/flow_followup.md)
- [lint_service](../modules/lint_service.md)
- [plugins](../modules/plugins.md)

## Behavior

This workflow starts at `lint_service._check_data_flow_diagnostics`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
