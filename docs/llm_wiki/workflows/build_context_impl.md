# build_context_impl

**Entry point:** `context_service._build_context_impl`
**Modules involved:** [context_request_format](../modules/context_request_format.md), [context_service](../modules/context_service.md), [documentation_query_builder](../modules/documentation_query_builder.md), [path_policy](../modules/path_policy.md), [source_retirement](../modules/source_retirement.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `path_policy.validate_source_root`
2. `path_policy.validate_path`
3. `context_request_format.ProtocolRequestError`
4. `source_selection.resolve_source_selection`
5. `source_snapshot.capture_source_selection_inputs`
6. `documentation_query_builder.validate_live_query_source_selection`
7. `context_request_format.ProtocolRequestError`
8. `context_request_format.ProtocolRequestError`
9. `context_request_format.ProtocolRequestError`
10. `source_snapshot.build_source_snapshot`
11. `source_retirement.retained_empty_module_paths_from_wiki`
12. `context_request_format.ProtocolRequestError`
13. `source_selection.resolve_source_selection`
14. `documentation_query_builder.validate_live_query_source_selection`
15. `context_request_format.ProtocolRequestError`
16. `context_request_format.ProtocolRequestError`
17. `context_request_format.ProtocolRequestError`

## Touches

- [context_request_format](../modules/context_request_format.md)
- [context_service](../modules/context_service.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [path_policy](../modules/path_policy.md)
- [source_retirement](../modules/source_retirement.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `context_service._build_context_impl`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
