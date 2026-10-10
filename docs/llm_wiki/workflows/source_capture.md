# source_capture

**Entry point:** `task_context_v2._source_capture`
**Modules involved:** [context_packet](../modules/context_packet.md), [documentation_query_builder](../modules/documentation_query_builder.md), [entrypoints](../modules/entrypoints.md), [extraction_service](../modules/extraction_service.md), [services_dependencies](../modules/services_dependencies.md), [source_snapshot](../modules/source_snapshot.md), [task_context_v2](../modules/task_context_v2.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.build_source_snapshot`
2. `context_packet._guard_windows_inputs`
3. `context_packet.ContextPacketUnavailableError`
4. `context_packet._source_anchor`
5. `context_packet._assert_source_inputs_unchanged`
6. `extraction_service.resolve_call_edges`
7. `entrypoints.get_entry_points`
8. `entrypoints.read_console_scripts`
9. `entrypoints.build_flow`
10. `services_dependencies.analyze_dependencies`
11. `documentation_query_builder.assemble_documentation_query_service`

## Touches

- [context_packet](../modules/context_packet.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_snapshot](../modules/source_snapshot.md)
- [task_context_v2](../modules/task_context_v2.md)

## Behavior

Captures the permitted source and configuration inputs, invokes the existing read-only extractors and builds pure declaration and graph query views. It checks source identity after extraction and leaves live publication to the task owner’s final validation.
