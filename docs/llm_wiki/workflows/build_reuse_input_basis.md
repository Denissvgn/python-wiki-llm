# build_reuse_input_basis

**Entry point:** `knowledge_reuse.build_reuse_input_basis`
**Modules involved:** [host](../modules/host.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_reuse](../modules/knowledge_reuse.md), [knowledge_reuse_format](../modules/knowledge_reuse_format.md)

> Capture the inputs of the deterministic built-in sync pipeline.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_evidence.is_valid_sha256`
2. `host.current_host`
3. `knowledge_orchestration.runtime_source_snapshot_hash`
4. `knowledge_envelope.hash_inventory`
5. `knowledge_orchestration.runtime_generation_options_hash`
6. `knowledge_reuse_format.repository_input_hash`
7. `knowledge_envelope.build_repository_record`

## Touches

- [host](../modules/host.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_reuse_format](../modules/knowledge_reuse_format.md)

## Behavior

This workflow starts at `knowledge_reuse.build_reuse_input_basis`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
