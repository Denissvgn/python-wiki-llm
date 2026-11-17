# build_budgeted_context

**Entry point:** `context_budget.build_budgeted_context`
**Modules involved:** [change_selection](../modules/change_selection.md), [context_budget](../modules/context_budget.md), [context_packet_builder](../modules/context_packet_builder.md), [context_request_format](../modules/context_request_format.md), [token_counting](../modules/token_counting.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `context_request_format.validate_budget_request`
2. `token_counting.EstimatedCounter`
3. `context_packet_builder.capture_context_read`
4. `change_selection.select_changes`
5. `change_selection.affected_page_map`
6. `context_packet_builder.build_context_from_captured_read`
7. `context_packet_builder._assert_source_unchanged`
8. `context_packet_builder._assert_wiki_unchanged`
9. `context_packet_builder._assert_selection_unchanged`

## Touches

- [change_selection](../modules/change_selection.md)
- [context_budget](../modules/context_budget.md)
- [context_packet_builder](../modules/context_packet_builder.md)
- [context_request_format](../modules/context_request_format.md)
- [token_counting](../modules/token_counting.md)

## Behavior

This workflow starts at `context_budget.build_budgeted_context`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
