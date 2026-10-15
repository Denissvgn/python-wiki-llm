# input_key

**Entry point:** `sync_analysis_cache.input_key`
**Modules involved:** [analysis_capture](../modules/analysis_capture.md), [knowledge_reuse](../modules/knowledge_reuse.md), [maintenance_state](../modules/maintenance_state.md), [sync_analysis_cache](../modules/sync_analysis_cache.md)

> Bind source bytes, policy, schema, producer, helpers and generation options.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `maintenance_state._identity`
2. `analysis_capture.capture_analysis`
3. `knowledge_reuse.implementation_hash`
4. `analysis_capture.analysis_diagnostics`

## Touches

- [analysis_capture](../modules/analysis_capture.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [maintenance_state](../modules/maintenance_state.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)

## Behavior

For an ordinary-maintenance snapshot, the function first requires a canonical
UUIDv4 adoption identity. Missing or invalid identity returns no cache key;
optional capture diagnostics explain the skip before any analysis probe. An
unadopted snapshot omits that owner binding. Surface initialization, explicit
storage-format requests, plugin locks and governance retain their existing
cache exclusions.

Eligible snapshots qualify the active language analysis and installed
implementation, then bind exact source hashes, input kinds, ignore and selection
policy, generation inputs and structural rendering options. The reuse metadata
field is excluded from its own key. A valid ordinary owner adds only its stable
identity; mutable review records and actor history remain under current owning
reconciliation. Returning a key neither writes a cache nor replaces native
authority validation. Unqualified analysis or implementation returns no key and
retains its bounded diagnostic when requested.
