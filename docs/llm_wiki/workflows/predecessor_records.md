# predecessor_records

**Entry point:** `historical_sources.predecessor_records`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [historical_sources](../modules/historical_sources.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md)

> Derive proof from a validated native predecessor, never from a client receipt.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_artifacts.require_validated_artifacts`
2. `knowledge_envelope.EvaluatedEnvelope`
3. `knowledge_evidence.hash_json`
4. `knowledge_evidence.is_valid_sha256`
5. `canonical_json.sha256_digest`
6. `canonical_json.sha256_digest`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [historical_sources](../modules/historical_sources.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)

## Behavior

This workflow starts at `historical_sources.predecessor_records`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
