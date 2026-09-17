# expand_storage_receipt

**Entry point:** `storage_receipts.expand_storage_receipt`
**Modules involved:** [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [storage_receipts](../modules/storage_receipts.md), [validation](../modules/validation.md)

> Expand compact proof data without evaluating its authority or freshness.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `validation.is_portable_relative_path`
2. `knowledge_packs.index_page_path`
3. `knowledge_packs.pack_path`
4. `knowledge_storage.canonical_bytes`
5. `knowledge_storage.canonical_bytes`

## Touches

- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [storage_receipts](../modules/storage_receipts.md)
- [validation](../modules/validation.md)

## Behavior

This workflow starts at `storage_receipts.expand_storage_receipt`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
