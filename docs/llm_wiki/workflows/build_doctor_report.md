# build_doctor_report

**Entry point:** `doctor_service.build_doctor_report`
**Modules involved:** [analysis_compatibility](../modules/analysis_compatibility.md), [doctor_service](../modules/doctor_service.md), [lint_service](../modules/lint_service.md), [path_policy](../modules/path_policy.md)

> Build a doctor report by composing existing strict-lint results.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `path_policy.validate_path`
2. `path_policy.validate_source_root`
3. `lint_service.build_report`
4. `analysis_compatibility.report_schema`

## Touches

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [doctor_service](../modules/doctor_service.md)
- [lint_service](../modules/lint_service.md)
- [path_policy](../modules/path_policy.md)

## Behavior

This workflow starts at `doctor_service.build_doctor_report`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
