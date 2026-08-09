# get_inventory

**Entry point:** `context_service.get_inventory`
**Modules involved:** [context_service](../modules/context_service.md), [extraction_jobs](../modules/extraction_jobs.md), [extraction_service](../modules/extraction_service.md), [source_snapshot](../modules/source_snapshot.md)

> Build command inventory, optionally returning extraction metadata.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extraction_jobs.ExtractionJobPlan`
2. `extraction_jobs.ExtractionJobRequest`
3. `source_snapshot.SourceSnapshot`
4. `extraction_service.InventoryResult`

## Touches

- [context_service](../modules/context_service.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

Adapts context requests to the shared extraction service. It forwards depth,
worker planning, plugin policy, source selection, and an optional captured
snapshot, then converts any failed extractor status into a field-specific
`ProtocolRequestError`. Callers may request the plain merged inventory or the
full `InventoryResult` when job, cache, producer, and snapshot metadata are
needed.
