# export_publication_candidate

**Entry point:** `publication_candidate.export_publication_candidate`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [publication_candidate](../modules/publication_candidate.md), [publication_config](../modules/publication_config.md), [publication_snapshot](../modules/publication_snapshot.md)

> Render a fresh local candidate, preserving every unmanaged target file.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_snapshot.assert_bootstrap_output_excluded`
2. `publication_config.publication_path`
3. `filesystem_guard.ensure_guarded_directory`
4. `filesystem_guard.ensure_guarded_directory`
5. `filesystem_guard.atomic_write_private_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_config](../modules/publication_config.md)
- [publication_snapshot](../modules/publication_snapshot.md)

## Behavior

This workflow starts at `publication_candidate.export_publication_candidate`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
