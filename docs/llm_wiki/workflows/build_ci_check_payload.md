# build_ci_check_payload

**Entry point:** `ci_report.build_ci_check_payload`
**Modules involved:** [analysis_compatibility](../modules/analysis_compatibility.md), [ci_report](../modules/ci_report.md), [doctor_service](../modules/doctor_service.md), [lint_service](../modules/lint_service.md)

> Compose versioned CI and doctor results from one evaluated lint report.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `analysis_compatibility.report_schema`
2. `lint_service.report_to_dict`
3. `doctor_service.compose_doctor_report`

## Touches

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [ci_report](../modules/ci_report.md)
- [doctor_service](../modules/doctor_service.md)
- [lint_service](../modules/lint_service.md)

## Behavior

This workflow starts at `ci_report.build_ci_check_payload`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
