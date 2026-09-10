# append_log

**Entry point:** `sync_cmd._append_log`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [io](../modules/io.md), [paths](../modules/paths.md), [sync_cmd](../modules/sync_cmd.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `bootstrap_runtime._source_snapshot_log_lines`
2. `paths.portable_source_root_label`
3. `io.read_md`
4. `io.write_md`
5. `io.write_md`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [io](../modules/io.md)
- [paths](../modules/paths.md)
- [sync_cmd](../modules/sync_cmd.md)

## Behavior

After page and index updates, this workflow appends one dated operation record
to `log.md`, creating the log header when the file is absent. It records a
portable source label, source-selection and producer details, page counters,
semantic preservation, and only the source, infrastructure, surface, move, or
retirement actions that were actually applied. Deferred work is counted as
deferred rather than reported as completed.
