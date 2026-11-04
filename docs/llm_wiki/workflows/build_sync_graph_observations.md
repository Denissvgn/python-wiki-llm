# build_sync_graph_observations

**Entry point:** `sync_cmd._build_sync_graph_observations`
**Modules involved:** [data_flow](../modules/data_flow.md), [entrypoints](../modules/entrypoints.md), [extraction_service](../modules/extraction_service.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [services_dependencies](../modules/services_dependencies.md), [sync_cmd](../modules/sync_cmd.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extraction_service.resolve_call_edges`
2. `extraction_service.resolve_call_observations`
3. `entrypoints.build_flow_context`
4. `entrypoints.build_flow`
5. `entrypoints.build_flow_detailed`
6. `knowledge_orchestration.runtime_generation_options`
7. `data_flow.build_data_flow_context`
8. `data_flow.analyze_data_flow`
9. `data_flow.analyze_data_flow_detailed`
10. `entrypoints.build_flow`
11. `data_flow.analyze_data_flow`
12. `knowledge_orchestration.runtime_graph_analyzer_limitations`
13. `services_dependencies.build_dependency_observations`
14. `services_dependencies.build_external_dependency_observations`

## Touches

- [data_flow](../modules/data_flow.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [services_dependencies](../modules/services_dependencies.md)
- [sync_cmd](../modules/sync_cmd.md)

## Behavior

This workflow starts at `sync_cmd._build_sync_graph_observations`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
