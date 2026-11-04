# completed_inventory_result

**Entry point:** `extraction_service._completed_inventory_result`
**Modules involved:** [analysis_capture](../modules/analysis_capture.md), [extraction_service](../modules/extraction_service.md), [inventory_cache](../modules/inventory_cache.md), [progress](../modules/progress.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `progress.record_counts`
2. `progress.record_counts`
3. `analysis_capture.capture_analysis`
4. `inventory_cache.extraction_bundle_hash`

## Touches

- [analysis_capture](../modules/analysis_capture.md)
- [extraction_service](../modules/extraction_service.md)
- [inventory_cache](../modules/inventory_cache.md)
- [progress](../modules/progress.md)

## Behavior

This workflow starts at `extraction_service._completed_inventory_result`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
