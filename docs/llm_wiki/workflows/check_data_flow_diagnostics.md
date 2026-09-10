# check_data_flow_diagnostics

**Entry point:** `lint_service._check_data_flow_diagnostics`
**Modules involved:** [data_flow](../modules/data_flow.md), [entrypoints](../modules/entrypoints.md), [extraction_service](../modules/extraction_service.md), [lint_service](../modules/lint_service.md), [plugins](../modules/plugins.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extraction_service.resolve_call_edges`
2. `entrypoints.get_entry_points`
3. `entrypoints.read_console_scripts`
4. `plugins.runtime_plugin_fallback_root`
5. `data_flow.analyze_data_flow`
6. `entrypoints.build_flow`

## Touches

- [data_flow](../modules/data_flow.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [lint_service](../modules/lint_service.md)
- [plugins](../modules/plugins.md)

## Behavior

This workflow starts at `lint_service._check_data_flow_diagnostics`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
