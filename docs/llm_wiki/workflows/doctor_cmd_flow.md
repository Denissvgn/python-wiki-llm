# doctor_cmd_flow

**Entry point:** `doctor_cmd.run`
**Modules involved:** [capability_diagnostics](../modules/capability_diagnostics.md), [doctor_cmd](../modules/doctor_cmd.md), [doctor_service](../modules/doctor_service.md), [extraction_jobs](../modules/extraction_jobs.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `capability_diagnostics.build_capability_doctor`
2. `extraction_jobs.extraction_job_request_from_args`
3. `capability_diagnostics.render_capability_doctor`
4. `doctor_service.build_doctor_report`
5. `extraction_jobs.extraction_job_request_from_args`
6. `doctor_service.render_doctor_text`

## Touches

- [capability_diagnostics](../modules/capability_diagnostics.md)
- [doctor_cmd](../modules/doctor_cmd.md)
- [doctor_service](../modules/doctor_service.md)
- [extraction_jobs](../modules/extraction_jobs.md)

## Behavior

This workflow starts at `doctor_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
