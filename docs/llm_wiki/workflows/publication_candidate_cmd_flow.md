# publication_candidate_cmd_flow

**Entry point:** `publication_candidate_cmd.run`
**Modules involved:** [publication_candidate](../modules/publication_candidate.md), [publication_candidate_cmd](../modules/publication_candidate_cmd.md), [publication_cmd](../modules/publication_cmd.md), [publication_contracts](../modules/publication_contracts.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_candidate.validate_publication_receipt`
2. `publication_candidate.validate_candidate_tree`
3. `publication_candidate.validate_candidate_target`
4. `publication_candidate.review_publication_candidate`
5. `publication_cmd._document_bytes`
6. `publication_contracts.validate_publication_basis`
7. `publication_candidate.validate_publication_receipt`
8. `publication_candidate.export_publication_candidate`
9. `publication_candidate.check_publication_candidate`
10. `publication_cmd._document_bytes`

## Touches

- [publication_candidate](../modules/publication_candidate.md)
- [publication_candidate_cmd](../modules/publication_candidate_cmd.md)
- [publication_cmd](../modules/publication_cmd.md)
- [publication_contracts](../modules/publication_contracts.md)

## Behavior

This workflow starts at `publication_candidate_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
