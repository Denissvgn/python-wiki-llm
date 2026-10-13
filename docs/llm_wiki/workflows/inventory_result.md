# inventory_result

**Entry point:** `sync_analysis_cache.inventory_result`
**Modules involved:** [analysis_capture](../modules/analysis_capture.md), [extraction_service](../modules/extraction_service.md), [inventory_cache](../modules/inventory_cache.md), [sync_analysis_cache](../modules/sync_analysis_cache.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `analysis_capture.capture_analysis`
2. `extraction_service.InventoryResult`
3. `extraction_service.ExtractorStatus`
4. `inventory_cache.InventoryCacheStats`

## Touches

- [analysis_capture](../modules/analysis_capture.md)
- [extraction_service](../modules/extraction_service.md)
- [inventory_cache](../modules/inventory_cache.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)

## Behavior

This workflow starts at `sync_analysis_cache.inventory_result`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
