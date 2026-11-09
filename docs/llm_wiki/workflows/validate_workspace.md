# validate_workspace

**Entry point:** `publication_maintenance._validate_workspace`
**Modules involved:** [integrity](../modules/integrity.md), [publication_candidate](../modules/publication_candidate.md), [publication_config](../modules/publication_config.md), [publication_maintenance](../modules/publication_maintenance.md), [source_selection](../modules/source_selection.md), [workspace](../modules/workspace.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_config.publication_control_overlap`
2. `publication_candidate._candidate_path`
3. `workspace.load_documentation_run`
4. `workspace._load_bound_runtime_policy`
5. `publication_config.publication_path`
6. `source_selection.resolve_source_selection`
7. `publication_config.publication_path`
8. `integrity._verify_read_only_inputs`

## Touches

- [integrity](../modules/integrity.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_config](../modules/publication_config.md)
- [publication_maintenance](../modules/publication_maintenance.md)
- [source_selection](../modules/source_selection.md)
- [workspace](../modules/workspace.md)

## Behavior

This workflow starts at `publication_maintenance._validate_workspace`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
