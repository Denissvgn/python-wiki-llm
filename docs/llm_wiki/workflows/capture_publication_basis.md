# capture_publication_basis

**Entry point:** `publication_impact.capture_publication_basis`
**Modules involved:** [knowledge_storage_io](../modules/knowledge_storage_io.md), [publication_config](../modules/publication_config.md), [publication_contracts](../modules/publication_contracts.md), [publication_impact](../modules/publication_impact.md), [publication_references](../modules/publication_references.md)

> Capture a portable input basis without extraction or remote access.

The native wiki must be populated by its owning workflow first. A source-only
consumer may point architecture.root at an isolated bootstrap output.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_config.load_publication_config`
2. `publication_contracts.validate_publication_basis`
3. `publication_config.publication_path`
4. `knowledge_storage_io.StorageReadSession`
5. `publication_references.capture_reference_inputs`
6. `publication_config.publication_path`
7. `publication_contracts.PublicationProtocolError`
8. `knowledge_storage_io.StorageReadSession`
9. `publication_contracts.PublicationProtocolError`
10. `publication_references.recheck_reference_inputs`
11. `publication_config.publication_path`
12. `publication_contracts.PublicationProtocolError`
13. `publication_config.publication_path`
14. `publication_contracts.PublicationProtocolError`
15. `publication_config.load_publication_config`
16. `publication_contracts.PublicationProtocolError`
17. `publication_contracts.validate_publication_basis`

## Touches

- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication_config](../modules/publication_config.md)
- [publication_contracts](../modules/publication_contracts.md)
- [publication_impact](../modules/publication_impact.md)
- [publication_references](../modules/publication_references.md)

## Behavior

This workflow starts at `publication_impact.capture_publication_basis`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
