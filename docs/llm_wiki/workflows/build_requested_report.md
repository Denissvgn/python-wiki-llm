# build_requested_report

**Entry point:** `lint_service._build_requested_report`
**Modules involved:** [extraction_jobs](../modules/extraction_jobs.md), [inventory_cache](../modules/inventory_cache.md), [lint_service](../modules/lint_service.md), [path_policy](../modules/path_policy.md)

> Validate the request's paths and build its report; paths may raise.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `path_policy.validate_path`
2. `path_policy.validate_source_root`
3. `inventory_cache.cache_options_for`
4. `extraction_jobs.extraction_job_request_for`

## Touches

- [extraction_jobs](../modules/extraction_jobs.md)
- [inventory_cache](../modules/inventory_cache.md)
- [lint_service](../modules/lint_service.md)
- [path_policy](../modules/path_policy.md)

## Behavior

This workflow starts at `lint_service._build_requested_report`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
