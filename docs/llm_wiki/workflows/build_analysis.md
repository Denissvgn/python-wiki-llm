# build_analysis

**Entry point:** `review_service.build_analysis`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [change_selection](../modules/change_selection.md), [extraction_service](../modules/extraction_service.md), [review_service](../modules/review_service.md), [source_snapshot](../modules/source_snapshot.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extraction_service.filter_source_diff`
2. `change_selection.select_changes`
3. `change_selection.source_relative_paths`
4. `change_selection.select_changes`
5. `source_snapshot.source_snapshot_matches_current_files`
6. `change_selection._git`
7. `extraction_service.get_inventory_result`
8. `bootstrap_runtime.build_module_page_map`
9. `bootstrap_runtime.build_entity_page_map`
10. `bootstrap_runtime.build_entity_occurrence_page_map`
11. `change_selection.affected_page_map`
12. `change_selection.source_relative_paths`
13. `wiki_surface.collect_wiki_pages`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [change_selection](../modules/change_selection.md)
- [extraction_service](../modules/extraction_service.md)
- [review_service](../modules/review_service.md)
- [source_snapshot](../modules/source_snapshot.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `review_service.build_analysis`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.

Classifies requested changes before requesting deep inventory. Excluded-only
configured scope yields bounded metadata and unknown native coverage, not a
no-impact verdict. Other scope retains full source and helper checks.
Source/profile mutation still refuses the result, and failed classification
stays explicit even when the full inventory is available.
