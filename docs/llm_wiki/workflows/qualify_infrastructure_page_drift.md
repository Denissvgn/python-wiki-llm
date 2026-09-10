# qualify_infrastructure_page_drift

**Entry point:** `sync_cmd._qualify_infrastructure_page_drift`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [io](../modules/io.md), [source_snapshot](../modules/source_snapshot.md), [sync_cmd](../modules/sync_cmd.md)

> Promote page drift without treating the semantic Notes body as generated.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.unsupported_source_summary`
2. `io.read_md`
3. `bootstrap_runtime._generate_infrastructure_md`
4. `io.read_md`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [io](../modules/io.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_cmd](../modules/sync_cmd.md)

## Behavior

This workflow starts at `sync_cmd._qualify_infrastructure_page_drift`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
