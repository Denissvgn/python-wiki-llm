# sync_run_options_from_args

**Entry point:** `sync_cmd._sync_run_options_from_args`
**Modules involved:** [config](../modules/config.md), [extraction_jobs](../modules/extraction_jobs.md), [inventory_cache](../modules/inventory_cache.md), [sync_cmd](../modules/sync_cmd.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `inventory_cache.InventoryCacheOptions`
2. `extraction_jobs.extraction_job_request_from_args`
3. `config.validate_source_root`
4. `config.validate_path`

## Touches

- [config](../modules/config.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [inventory_cache](../modules/inventory_cache.md)
- [sync_cmd](../modules/sync_cmd.md)

## Behavior

This workflow starts at `sync_cmd._sync_run_options_from_args`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
