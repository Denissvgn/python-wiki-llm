# main

**Entry point:** `cli.main`
**Modules involved:** [analysis_compatibility](../modules/analysis_compatibility.md), [cli](../modules/cli.md), [cli_declarations](../modules/cli_declarations.md), [helper_runtime](../modules/helper_runtime.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `cli_declarations._build_parser`
2. `analysis_compatibility.comparison_scope`
3. `helper_runtime.helper_operation`

## Touches

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [cli](../modules/cli.md)
- [cli_declarations](../modules/cli_declarations.md)
- [helper_runtime](../modules/helper_runtime.md)

## Behavior

This workflow starts at `cli.main`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
