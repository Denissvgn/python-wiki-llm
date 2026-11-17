# context_service_flow

**Entry point:** `context_service.run`
**Modules involved:** [change_selection](../modules/change_selection.md), [context_budget](../modules/context_budget.md), [context_service](../modules/context_service.md), [extraction_jobs](../modules/extraction_jobs.md), [host](../modules/host.md), [io](../modules/io.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `host.emit`
2. `host.emit`
3. `change_selection.changes_from_args`
4. `context_budget.run`
5. `extraction_jobs.ExtractionJobRequest.resolved`
6. `host.emit`
7. `host.emit`
8. `io.write_text_output`
9. `host.emit`
10. `host.emit`
11. `io.write_text_output`
12. `host.emit`
13. `host.emit`

## Touches

- [change_selection](../modules/change_selection.md)
- [context_budget](../modules/context_budget.md)
- [context_service](../modules/context_service.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [host](../modules/host.md)
- [io](../modules/io.md)

## Behavior

This workflow starts at `context_service.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
