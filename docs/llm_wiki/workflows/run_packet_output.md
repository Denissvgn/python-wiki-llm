# run_packet_output

**Entry point:** `context_service._run_packet_output`
**Modules involved:** [context_packet](../modules/context_packet.md), [context_service](../modules/context_service.md), [extraction_jobs](../modules/extraction_jobs.md), [io](../modules/io.md)

> Build and emit canonical QCP bytes for the CLI-only packet format.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `context_packet.build_qualified_context`
2. `extraction_jobs.ExtractionJobRequest.resolved`
3. `io.write_text_output`

## Touches

- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [io](../modules/io.md)

## Behavior

This workflow starts at `context_service._run_packet_output`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
