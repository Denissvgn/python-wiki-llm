# build_budgeted_context

**Entry point:** `context_budget.build_budgeted_context`
**Modules involved:** [change_selection](../modules/change_selection.md), [context_budget](../modules/context_budget.md), [context_packet](../modules/context_packet.md), [token_counting](../modules/token_counting.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `token_counting.EstimatedCounter`
2. `context_packet.capture_context_read`
3. `change_selection.select_changes`
4. `change_selection.affected_page_map`
5. `context_packet.build_context_from_captured_read`
6. `context_packet._assert_source_unchanged`
7. `context_packet._assert_wiki_unchanged`
8. `context_packet._assert_selection_unchanged`

## Touches

- [change_selection](../modules/change_selection.md)
- [context_budget](../modules/context_budget.md)
- [context_packet](../modules/context_packet.md)
- [token_counting](../modules/token_counting.md)

## Behavior

This workflow starts at `context_budget.build_budgeted_context`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
