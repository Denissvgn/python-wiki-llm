# generate_bootstrap_content

**Entry point:** `bootstrap_runtime._generate_bootstrap_content`
**Modules involved:** [api_contracts](../modules/api_contracts.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [extraction_service](../modules/extraction_service.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_reuse](../modules/knowledge_reuse.md), [module_maps](../modules/module_maps.md), [services_dependencies](../modules/services_dependencies.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extraction_service.resolve_call_edges`
2. `extraction_service.resolve_call_observations`
3. `services_dependencies.build_dependency_observations`
4. `services_dependencies.build_external_dependency_observations`
5. `knowledge_orchestration.runtime_graph_analyzer_limitations`
6. `module_maps.build_module_dependency_maps`
7. `api_contracts.link_entry_point_flows`
8. `knowledge_reuse.observation_inputs_hash`

## Touches

- [api_contracts](../modules/api_contracts.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [extraction_service](../modules/extraction_service.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [module_maps](../modules/module_maps.md)
- [services_dependencies](../modules/services_dependencies.md)

## Behavior

This workflow starts at `bootstrap_runtime._generate_bootstrap_content`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
