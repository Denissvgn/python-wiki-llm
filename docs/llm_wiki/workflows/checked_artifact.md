# checked_artifact

**Entry point:** `publish.checked_artifact`
**Modules involved:** [publication_candidate](../modules/publication_candidate.md), [publication_config](../modules/publication_config.md), [publication_impact](../modules/publication_impact.md), [publish](../modules/publish.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_impact.read_publication_document`
2. `publication_candidate.validate_publication_receipt`
3. `publication_config.read_publication_json`
4. `publication_config.read_publication_json`
5. `publication_config.read_publication_json`
6. `publication_candidate._provider`

## Touches

- [publication_candidate](../modules/publication_candidate.md)
- [publication_config](../modules/publication_config.md)
- [publication_impact](../modules/publication_impact.md)
- [publish](../modules/publish.md)

## Behavior

This workflow starts at `publish.checked_artifact`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
