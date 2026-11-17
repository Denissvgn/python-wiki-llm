# native_bindings

**Entry point:** `task_implementation.native_bindings`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [implementation_evidence](../modules/implementation_evidence.md), [knowledge_storage](../modules/knowledge_storage.md), [task_implementation](../modules/task_implementation.md)

> Extract owner bindings from consumed native records, never display names.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `implementation_evidence.validate_implementation_evidence`
2. `canonical_json.sha256_digest`
3. `knowledge_storage.canonical_bytes`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [task_implementation](../modules/task_implementation.md)

## Behavior

This workflow starts at `task_implementation.native_bindings`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
