# explanation_provenance

**Entry point:** `evidence_explanation.explanation_provenance`
**Modules involved:** [analysis_capture](../modules/analysis_capture.md), [evidence_explanation](../modules/evidence_explanation.md), [extractor_helpers](../modules/extractor_helpers.md), [knowledge_reuse](../modules/knowledge_reuse.md)

> Keep observed installation, stored/live producers and runtime distinct.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extractor_helpers.helper_identity`
2. `analysis_capture.registry`
3. `knowledge_reuse.implementation_hash`

## Touches

- [analysis_capture](../modules/analysis_capture.md)
- [evidence_explanation](../modules/evidence_explanation.md)
- [extractor_helpers](../modules/extractor_helpers.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)

## Behavior

This workflow starts at `evidence_explanation.explanation_provenance`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
