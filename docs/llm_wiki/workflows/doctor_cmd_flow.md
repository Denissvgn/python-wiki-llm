# doctor_cmd_flow

**Entry point:** `doctor_cmd.run`
**Modules involved:** [analysis_targets](../modules/analysis_targets.md), [api](../modules/api.md), [capability_diagnostics](../modules/capability_diagnostics.md), [config](../modules/config.md), [doctor_cmd](../modules/doctor_cmd.md), [doctor_service](../modules/doctor_service.md), [extraction_jobs](../modules/extraction_jobs.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_path`
2. `config.validate_path`
3. `analysis_targets.inspect_targets`
4. `analysis_targets.load_targets`
5. `api.get_analysis_input_status`
6. `capability_diagnostics.build_capability_doctor`
7. `extraction_jobs.extraction_job_request_from_args`
8. `capability_diagnostics.render_capability_doctor`
9. `doctor_service.build_doctor_report`
10. `extraction_jobs.extraction_job_request_from_args`
11. `doctor_service.render_doctor_text`

## Touches

- [analysis_targets](../modules/analysis_targets.md)
- [api](../modules/api.md)
- [capability_diagnostics](../modules/capability_diagnostics.md)
- [config](../modules/config.md)
- [doctor_cmd](../modules/doctor_cmd.md)
- [doctor_service](../modules/doctor_service.md)
- [extraction_jobs](../modules/extraction_jobs.md)

## Behavior

This workflow starts at `doctor_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.

The target-runtime branch is exclusive with other doctor contracts and cannot replace strict health or explicit comparison-policy evaluation. It validates paths, loads bounded project-owned declarations, inspects committed producer metadata and returns qualified text/JSON. It does not perform source extraction, target execution, setup or repair; unknowns stay unresolved and matching declarations do not qualify a target host.
