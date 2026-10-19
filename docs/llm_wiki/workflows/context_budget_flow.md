# context_budget_flow

**Entry point:** `context_budget.run`
**Modules involved:** [change_selection](../modules/change_selection.md), [context_budget](../modules/context_budget.md), [context_service](../modules/context_service.md), [io](../modules/io.md), [token_counting](../modules/token_counting.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `change_selection.changes_from_args`
2. `change_selection.changes_from_args`
3. `token_counting.LocalTokenizerCounter`
4. `context_service._emit_packet_error`
5. `io.write_text_output`
6. `io.write_utf8_stdout`

## Touches

- [change_selection](../modules/change_selection.md)
- [context_budget](../modules/context_budget.md)
- [context_service](../modules/context_service.md)
- [io](../modules/io.md)
- [token_counting](../modules/token_counting.md)

## Behavior

Builds the normalized complete-output request and selects the trusted counter before invoking the shared captured-context builder. A typed ordinary-authority refusal uses the same bounded diagnostic as raw packet delivery, emits JSON on stderr and leaves stdout and any existing output file untouched. It does not retry recovery or weaken required native evidence. Successful results retain their counted rendering; cannot-fit keeps its distinct accounting and exit behavior.
