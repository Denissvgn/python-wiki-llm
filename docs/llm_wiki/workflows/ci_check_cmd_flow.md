# ci_check_cmd_flow

**Entry point:** `ci_check_cmd.run`
**Modules involved:** [ci_check_cmd](../modules/ci_check_cmd.md), [config](../modules/config.md), [extraction_jobs](../modules/extraction_jobs.md), [inventory_cache](../modules/inventory_cache.md), [lint_service](../modules/lint_service.md), [metrics](../modules/metrics.md), [runtime_output](../modules/runtime_output.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `runtime_output.RuntimeOutputError`
2. `config.validate_source_root`
3. `config.validate_path`
4. `inventory_cache.cache_options_from_args`
5. `inventory_cache.prepare_cache_options`
6. `extraction_jobs.extraction_job_request_from_args`
7. `lint_service.build_report`
8. `inventory_cache.InventoryCacheStats`
9. `inventory_cache.format_cache_stats`
10. `metrics.record_validation_event`

## Touches

- [ci_check_cmd](../modules/ci_check_cmd.md)
- [config](../modules/config.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [inventory_cache](../modules/inventory_cache.md)
- [lint_service](../modules/lint_service.md)
- [metrics](../modules/metrics.md)
- [runtime_output](../modules/runtime_output.md)

## Behavior

This workflow starts at `ci_check_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
