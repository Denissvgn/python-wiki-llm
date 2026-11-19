# run_protocol

**Entry point:** `context_service._run_protocol`
**Modules involved:** [change_selection](../modules/change_selection.md), [context_budget](../modules/context_budget.md), [context_request_format](../modules/context_request_format.md), [context_service](../modules/context_service.md), [extraction_jobs](../modules/extraction_jobs.md), [host](../modules/host.md), [io](../modules/io.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `context_request_format.ProtocolRequestError`
2. `context_budget.run`
3. `change_selection.changes_from_args`
4. `context_request_format.ProtocolRequestError`
5. `extraction_jobs.ExtractionJobRequest.resolved`
6. `host.emit`
7. `io.write_text_output`
8. `host.emit`
9. `host.emit`

## Touches

- [change_selection](../modules/change_selection.md)
- [context_budget](../modules/context_budget.md)
- [context_request_format](../modules/context_request_format.md)
- [context_service](../modules/context_service.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [host](../modules/host.md)
- [io](../modules/io.md)

## Behavior

This workflow starts at `context_service._run_protocol`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
