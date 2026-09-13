# run_protocol

**Entry point:** `context_service._run_protocol`
**Modules involved:** [change_selection](../modules/change_selection.md), [context_budget](../modules/context_budget.md), [context_service](../modules/context_service.md), [extraction_jobs](../modules/extraction_jobs.md), [io](../modules/io.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `context_budget.run`
2. `change_selection.changes_from_args`
3. `extraction_jobs.ExtractionJobRequest.resolved`
4. `io.write_text_output`

## Touches

- [change_selection](../modules/change_selection.md)
- [context_budget](../modules/context_budget.md)
- [context_service](../modules/context_service.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [io](../modules/io.md)

## Behavior

This workflow starts at `context_service._run_protocol`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
