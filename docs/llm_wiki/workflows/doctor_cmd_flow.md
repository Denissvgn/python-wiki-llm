# doctor_cmd_flow

**Entry point:** `doctor_cmd.run`
**Modules involved:** [api](../modules/api.md), [capability_diagnostics](../modules/capability_diagnostics.md), [doctor_cmd](../modules/doctor_cmd.md), [doctor_service](../modules/doctor_service.md), [extraction_jobs](../modules/extraction_jobs.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `api.get_analysis_input_status`
2. `capability_diagnostics.build_capability_doctor`
3. `extraction_jobs.extraction_job_request_from_args`
4. `capability_diagnostics.render_capability_doctor`
5. `doctor_service.build_doctor_report`
6. `extraction_jobs.extraction_job_request_from_args`
7. `doctor_service.render_doctor_text`

## Touches

- [api](../modules/api.md)
- [capability_diagnostics](../modules/capability_diagnostics.md)
- [doctor_cmd](../modules/doctor_cmd.md)
- [doctor_service](../modules/doctor_service.md)
- [extraction_jobs](../modules/extraction_jobs.md)

## Behavior

This workflow starts at `doctor_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
