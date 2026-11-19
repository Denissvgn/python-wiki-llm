# publication_target_observation

**Entry point:** `publication_impact.publication_target_observation`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [publication_contracts](../modules/publication_contracts.md), [publication_impact](../modules/publication_impact.md), [publication_links](../modules/publication_links.md)

> Commit supplied public bytes without filesystem or remote access.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_contracts.PublicationProtocolError`
2. `canonical_json.sha256_digest`
3. `publication_links.public_atx_section`
4. `publication_contracts.PublicationProtocolError`
5. `canonical_json.sha256_digest`
6. `canonical_json.sha256_digest`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [publication_contracts](../modules/publication_contracts.md)
- [publication_impact](../modules/publication_impact.md)
- [publication_links](../modules/publication_links.md)

## Behavior

This workflow starts at `publication_impact.publication_target_observation`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
