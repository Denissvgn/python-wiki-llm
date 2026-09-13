# build_impact

**Entry point:** `impact.build_impact`
**Modules involved:** [api_contracts](../modules/api_contracts.md), [change_selection](../modules/change_selection.md), [impact](../modules/impact.md), [review_service](../modules/review_service.md), [services_dependencies](../modules/services_dependencies.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `change_selection.source_relative_paths`
2. `change_selection.patch_paths`
3. `review_service.build_analysis`
4. `services_dependencies.build_dependency_graph`
5. `api_contracts.build_static_api_contracts`
6. `change_selection._git`
7. `review_service._is_dependency_path`
8. `source_snapshot.source_snapshot_matches_current_files`

## Touches

- [api_contracts](../modules/api_contracts.md)
- [change_selection](../modules/change_selection.md)
- [impact](../modules/impact.md)
- [review_service](../modules/review_service.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `impact.build_impact`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
