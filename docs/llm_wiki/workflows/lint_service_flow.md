# lint_service_flow

**Entry point:** `lint_service.run`
**Modules involved:** [config](../modules/config.md), [extraction_jobs](../modules/extraction_jobs.md), [inventory_cache](../modules/inventory_cache.md), [lint_service](../modules/lint_service.md), [metrics](../modules/metrics.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_path`
2. `config.validate_source_root`
3. `inventory_cache.cache_options_from_args`
4. `extraction_jobs.extraction_job_request_from_args`
5. `metrics.record_validation_event`

## Touches

- [config](../modules/config.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [inventory_cache](../modules/inventory_cache.md)
- [lint_service](../modules/lint_service.md)
- [metrics](../modules/metrics.md)

## Behavior

This workflow starts at `lint_service.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
