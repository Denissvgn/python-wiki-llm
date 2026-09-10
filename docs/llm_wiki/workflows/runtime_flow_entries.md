# runtime_flow_entries

**Entry point:** `documentation_native._runtime_flow_entries`
**Modules involved:** [api_contracts](../modules/api_contracts.md), [data_flow](../modules/data_flow.md), [documentation_native](../modules/documentation_native.md), [entrypoints](../modules/entrypoints.md), [extraction_service](../modules/extraction_service.md), [paths](../modules/paths.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `entrypoints.detect_entry_points`
2. `entrypoints.read_console_scripts`
3. `paths.is_test_source_path`
4. `api_contracts.attach_routes_to_entry_points`
5. `extraction_service.resolve_call_edges`
6. `data_flow.build_data_flow_context`
7. `entrypoints.build_flow`
8. `data_flow.analyze_data_flow`

## Touches

- [api_contracts](../modules/api_contracts.md)
- [data_flow](../modules/data_flow.md)
- [documentation_native](../modules/documentation_native.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [paths](../modules/paths.md)

## Behavior

This workflow starts at `documentation_native._runtime_flow_entries`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
