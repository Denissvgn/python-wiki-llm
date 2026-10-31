# build_extract_payload

**Entry point:** `extraction_service.build_extract_payload`
**Modules involved:** [api_contracts](../modules/api_contracts.md), [common](../modules/common.md), [config](../modules/config.md), [data_flow](../modules/data_flow.md), [entrypoints](../modules/entrypoints.md), [extraction_service](../modules/extraction_service.md), [plugins](../modules/plugins.md), [services_dependencies](../modules/services_dependencies.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

> Build the stable extract JSON payload without printing or exiting.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_source_root`
2. `config.validate_source_paths`
3. `source_selection.resolve_source_selection`
4. `common.normalize_include_tests`
5. `services_dependencies.analyze_dependencies`
6. `api_contracts.build_api_contracts`
7. `source_snapshot.unsupported_source_summary`
8. `source_snapshot.unsupported_source_summary`
9. `api_contracts.build_api_contracts`
10. `plugins.runtime_project_plugins_enabled`
11. `entrypoints.read_console_scripts`
12. `entrypoints.detect_entry_points`
13. `api_contracts.attach_routes_to_entry_points`
14. `data_flow.build_data_flow_context`
15. `data_flow.analyze_data_flow_detailed`
16. `entrypoints.build_flow_detailed`
17. `data_flow.analyze_data_flow`
18. `entrypoints.build_flow`
19. `services_dependencies.analyze_dependencies`

## Touches

- [api_contracts](../modules/api_contracts.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [plugins](../modules/plugins.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `extraction_service.build_extract_payload`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
