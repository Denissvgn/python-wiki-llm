# write_bootstrap_flow_pages

**Entry point:** `bootstrap_runtime._write_bootstrap_flow_pages`
**Modules involved:** [api_contracts](../modules/api_contracts.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [data_flow](../modules/data_flow.md), [entrypoints](../modules/entrypoints.md), [extraction_service](../modules/extraction_service.md), [io](../modules/io.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `entrypoints.read_console_scripts`
2. `entrypoints.get_detailed_entry_points`
3. `api_contracts.attach_routes_to_entry_points`
4. `entrypoints.entry_points_from_detailed_observations`
5. `extraction_service.resolve_call_edges`
6. `data_flow.build_data_flow_context`
7. `entrypoints.build_flow`
8. `entrypoints.build_flow_detailed`
9. `data_flow.analyze_data_flow`
10. `data_flow.analyze_data_flow_detailed`
11. `io.read_md`

## Touches

- [api_contracts](../modules/api_contracts.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [data_flow](../modules/data_flow.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [io](../modules/io.md)

## Behavior

This workflow starts at `bootstrap_runtime._write_bootstrap_flow_pages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
