# build_generated_section_context

**Entry point:** `sync_cmd._build_generated_section_context`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [extraction_service](../modules/extraction_service.md), [module_maps](../modules/module_maps.md), [sync_cmd](../modules/sync_cmd.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extraction_service.resolve_call_edges`
2. `bootstrap_runtime._build_entity_relationship_summary_map`
3. `module_maps.build_module_dependency_maps`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [extraction_service](../modules/extraction_service.md)
- [module_maps](../modules/module_maps.md)
- [sync_cmd](../modules/sync_cmd.md)

## Behavior

This workflow starts at `sync_cmd._build_generated_section_context`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
