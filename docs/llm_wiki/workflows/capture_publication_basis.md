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
4. `publication_config.publication_path`
5. `knowledge_storage_io.StorageReadSession`
6. `publication_references.capture_reference_inputs`
7. `publication_config.publication_path`
8. `publication_contracts.PublicationProtocolError`
9. `knowledge_storage_io.StorageReadSession`
10. `publication_contracts.PublicationProtocolError`
11. `publication_references.recheck_reference_inputs`
12. `publication_config.publication_path`
13. `publication_contracts.PublicationProtocolError`
14. `publication_config.publication_path`
15. `publication_contracts.PublicationProtocolError`
16. `publication_config.load_publication_config`
17. `publication_contracts.PublicationProtocolError`
18. `publication_contracts.validate_publication_basis`

## Touches

- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication_config](../modules/publication_config.md)
- [publication_contracts](../modules/publication_contracts.md)
- [publication_impact](../modules/publication_impact.md)
- [publication_references](../modules/publication_references.md)

## Behavior

This workflow starts at `publication_impact.capture_publication_basis`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
