# publication_packet

**Entry point:** `publication.publication_packet`
**Modules involved:** [documentation_policy](../modules/documentation_policy.md), [documentation_run_contracts](../modules/documentation_run_contracts.md), [publication](../modules/publication.md), [workspace](../modules/workspace.md)

> Check the last accepted workspace before another packet can redefine its baseline.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `documentation_run_contracts.DocumentationIntegrityError`
2. `documentation_policy.hash_bytes`
3. `workspace._workspace_path`
4. `documentation_run_contracts.DocumentationIntegrityError`

## Touches

- [documentation_policy](../modules/documentation_policy.md)
- [documentation_run_contracts](../modules/documentation_run_contracts.md)
- [publication](../modules/publication.md)
- [workspace](../modules/workspace.md)

## Behavior

This workflow starts at `publication.publication_packet`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
