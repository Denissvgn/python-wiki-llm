# ci_check_cmd_flow

**Entry point:** `ci_check_cmd.run`
**Modules involved:** [ci_check_cmd](../modules/ci_check_cmd.md), [config](../modules/config.md), [extraction_jobs](../modules/extraction_jobs.md), [inventory_cache](../modules/inventory_cache.md), [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md), [lint_service](../modules/lint_service.md), [metrics](../modules/metrics.md), [runtime_output](../modules/runtime_output.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `runtime_output.RuntimeOutputError`
2. `runtime_output.RuntimeOutputError`
3. `config.validate_source_root`
4. `config.validate_path`
5. `inventory_cache.cache_options_from_args`
6. `inventory_cache.prepare_cache_options`
7. `extraction_jobs.extraction_job_request_from_args`
8. `lint_service.build_report`
9. `knowledge_storage_diagnostics.storage_report`
10. `lint_service.LintIssue`
11. `lint_service.LintIssue`
12. `lint_service.LintIssue`
13. `inventory_cache.InventoryCacheStats`
14. `inventory_cache.format_cache_stats`
15. `metrics.record_validation_event`

## Touches

- [ci_check_cmd](../modules/ci_check_cmd.md)
- [config](../modules/config.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [inventory_cache](../modules/inventory_cache.md)
- [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md)
- [lint_service](../modules/lint_service.md)
- [metrics](../modules/metrics.md)
- [runtime_output](../modules/runtime_output.md)

## Behavior

This workflow starts at `ci_check_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
