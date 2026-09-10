# persist_report

**Entry point:** `ci_check_cmd._persist_report`
**Modules involved:** [ci_check_cmd](../modules/ci_check_cmd.md), [io](../modules/io.md), [lint_service](../modules/lint_service.md), [runtime_output](../modules/runtime_output.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `io.write_bytes_atomic`
2. `lint_service.render_markdown`
3. `runtime_output.stderr_warning`

## Touches

- [ci_check_cmd](../modules/ci_check_cmd.md)
- [io](../modules/io.md)
- [lint_service](../modules/lint_service.md)
- [runtime_output](../modules/runtime_output.md)

## Behavior

This workflow starts at `ci_check_cmd._persist_report`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
