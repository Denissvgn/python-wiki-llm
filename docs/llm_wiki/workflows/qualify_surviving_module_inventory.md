# qualify_surviving_module_inventory

**Entry point:** `sync_runtime._qualify_surviving_module_inventory`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [host](../modules/host.md), [knowledge_evidence](../modules/knowledge_evidence.md), [source_retirement](../modules/source_retirement.md), [sync_runtime](../modules/sync_runtime.md)

> Resolve prior-owned sparse paths through attributable parser observations.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `host.emit`
2. `extraction_service.get_inventory_result`
3. `knowledge_evidence.module_observation_hash`
4. `source_retirement.SourceRetirementError`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [host](../modules/host.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [source_retirement](../modules/source_retirement.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

Selects missing prior-owned paths, member-boundary changes and retained cached
empty records lacking qualification. One narrow diagnostic extraction supplies
the actual module records. Empty promotion requires a successful built-in
provider, attributable outcome, complete module observation and empty declaration
arrays. Failed, unknown or alias outcomes stop before retirement writes.
