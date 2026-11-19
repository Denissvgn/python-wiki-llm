# DigestSession_read

**Entry point:** `knowledge_stream_audit._DigestSession.read`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_stream_audit](../modules/knowledge_stream_audit.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._require_relative_name`
2. `knowledge_storage_io.read_guarded`
3. `canonical_json.sha256_digest`
4. `knowledge_storage.KnowledgeStorageError`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_stream_audit](../modules/knowledge_stream_audit.md)

## Behavior

This workflow starts at `knowledge_stream_audit._DigestSession.read`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
