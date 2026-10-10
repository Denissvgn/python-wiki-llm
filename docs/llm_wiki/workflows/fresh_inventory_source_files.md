# fresh_inventory_source_files

**Entry point:** `extraction_service._fresh_inventory_source_files`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [inventory_cache](../modules/inventory_cache.md), [python_bindings](../modules/python_bindings.md), [python_observations](../modules/python_observations.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `inventory_cache.is_valid_cache_entry`
2. `python_bindings.valid_python_constructor_facts`
3. `python_observations.valid_cached_sidecars`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [inventory_cache](../modules/inventory_cache.md)
- [python_bindings](../modules/python_bindings.md)
- [python_observations](../modules/python_observations.md)

## Behavior

This workflow starts at `extraction_service._fresh_inventory_source_files`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
