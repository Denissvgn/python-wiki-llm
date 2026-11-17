# save_governance

**Entry point:** `knowledge_governance.save_governance`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md)

> Durably replace a ledger after an optional compare-and-swap check.

``expected_hash=None`` means the caller observed no prior ledger.
Omitting ``expected_hash`` is supported for low-level recovery tooling, but
all normal governance mutations should supply the hash they loaded while
holding :func:`governance_lock`.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `io.first_unsafe_path_component`
2. `canonical_json.sha256_digest`
3. `knowledge_evidence.is_valid_sha256`
4. `canonical_json.sha256_digest`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)

## Behavior

This workflow starts at `knowledge_governance.save_governance`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
