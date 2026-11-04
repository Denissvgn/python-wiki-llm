# valid_cached_implementation

**Entry point:** `extraction_service._valid_cached_implementation`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [implementation_evidence](../modules/implementation_evidence.md), [inventory_cache](../modules/inventory_cache.md), [knowledge_evidence](../modules/knowledge_evidence.md), [python_implementation](../modules/python_implementation.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `python_implementation.producer`
2. `inventory_cache.extraction_bundle_hash`
3. `knowledge_evidence.hash_json`
4. `implementation_evidence._row`
5. `python_implementation.comparison_id`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [inventory_cache](../modules/inventory_cache.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [python_implementation](../modules/python_implementation.md)

## Behavior

This workflow starts at `extraction_service._valid_cached_implementation`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
