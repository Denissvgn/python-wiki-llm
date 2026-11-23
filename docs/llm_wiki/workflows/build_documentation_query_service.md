# build_documentation_query_service

**Entry point:** `api.build_documentation_query_service`
**Modules involved:** [api](../modules/api.md), [documentation_query_builder](../modules/documentation_query_builder.md), [path_policy](../modules/path_policy.md), [query_request_format](../modules/query_request_format.md)

> Build a supported graph query service over derived documentation data.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `query_request_format.normalize_documentation_query_limit`
2. `path_policy.validate_source_root`
3. `documentation_query_builder.build_live_documentation_query_service`

## Touches

- [api](../modules/api.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [path_policy](../modules/path_policy.md)
- [query_request_format](../modules/query_request_format.md)

## Behavior

This workflow starts at `api.build_documentation_query_service`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
