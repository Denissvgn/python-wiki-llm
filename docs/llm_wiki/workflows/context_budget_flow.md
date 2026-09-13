# context_budget_flow

**Entry point:** `context_budget.run`
**Modules involved:** [change_selection](../modules/change_selection.md), [context_budget](../modules/context_budget.md), [io](../modules/io.md), [token_counting](../modules/token_counting.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `change_selection.changes_from_args`
2. `change_selection.changes_from_args`
3. `token_counting.LocalTokenizerCounter`
4. `io.write_text_output`

## Touches

- [change_selection](../modules/change_selection.md)
- [context_budget](../modules/context_budget.md)
- [io](../modules/io.md)
- [token_counting](../modules/token_counting.md)

## Behavior

This workflow starts at `context_budget.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
