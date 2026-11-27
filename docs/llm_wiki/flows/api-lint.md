# lint

**Entry point:** `lint` (`api`)
**Source:** [wiki_operations](../modules/wiki_operations.md)
**Modules touched:** [canonical_json](../modules/canonical_json.md), [filesystem_guard](../modules/filesystem_guard.md), [gitignore](../modules/gitignore.md), [integrations](../modules/integrations.md), and 10 more

**Complete modules touched:**

- [canonical_json](../modules/canonical_json.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [gitignore](../modules/gitignore.md)
- [integrations](../modules/integrations.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)
- [pack_interfaces](../modules/pack_interfaces.md)
- [path_policy](../modules/path_policy.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_operations](../modules/wiki_operations.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as lint
    participant p1 as _pack
    participant p2 as _roots
    participant p3 as SyncManifest.load
    participant p4 as _classified_sources
    participant p5 as _broken_links
    participant p6 as LintReport
    participant p7 as LintIssue
    participant p8 as _owned_pages
    participant p9 as _file_hash
    participant p10 as build_gitignore_matcher
    participant p11 as StorageReadSession.read
    participant p12 as SyncManifest.from_payload
    participant p13 as StorageReadSession.recheck
    participant p14 as _require_relative_name
    participant p15 as _mapping_value
    participant p16 as StorageReadSession.phase
    participant p17 as StorageReadSession.read_ranges
    participant p18 as ManifestStoreReader.materialize
    participant p19 as is_agent_worktree_path
    participant p20 as StorageReadSession.read_range
    participant p21 as _parse_gitignore_file
    participant p22 as _copy_sources
    participant p23 as _legacy_operational_state
    participant p24 as _validate_exact_keys
    participant p25 as _copy_mapping
    participant p26 as ManifestPageSource.from_payload
    participant p27 as ManifestEvidenceBaseline.from_payload
    participant p28 as ManifestTombstone.from_payload
    participant p29 as sorted (src/llm_wiki_engine/wiki_operations.py:lint)
    participant p30 as path.relative_to(…).as_posix (src/llm_wiki_engine/wiki_operations.py:lint)
    p0->>p1: _pack
    p0->>p2: _roots
    p0->>p3: SyncManifest.load
    p0->>p4: _classified_sources
    p0->>p5: _broken_links
    p0->>p6: LintReport
    p0->>p7: LintIssue
    p0->>p8: _owned_pages
    p0->>p9: _file_hash
    p4->>p10: build_gitignore_matcher
    p3->>p11: StorageReadSession.read
    p3->>p12: SyncManifest.from_payload
    p3->>p13: StorageReadSession.recheck
    p11->>p14: _require_relative_name
    p12->>p15: _mapping_value
    p13->>p16: StorageReadSession.phase
    p13->>p17: StorageReadSession.read_ranges
    p12->>p18: ManifestStoreReader.materialize
    p10->>p19: is_agent_worktree_path
    p13->>p20: StorageReadSession.read_range
    p10->>p21: _parse_gitignore_file
    p12->>p22: _copy_sources
    p12->>p23: _legacy_operational_state
    p12->>p24: _validate_exact_keys
    p12->>p25: _copy_mapping
    p12->>p26: ManifestPageSource.from_payload
    p12->>p27: ManifestEvidenceBaseline.from_payload
    p12->>p28: ManifestTombstone.from_payload
    p0-->>p29: sorted (src/llm_wiki_engine/wiki_operations.py:lint)(...)
    p0-->>p30: path.relative_to(…).as_posix (src/llm_wiki_engine/wiki_operations.py:lint)
```

> Call sequence diagram shows 30 of 528 interactions; 498 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 147 (146 omitted); unresolved 1 of 136 (135 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_engine/wiki_operations.py:_pack` | 2 | [src/llm_wiki_engine/pack_interfaces.py](../modules/pack_interfaces.md) | internal | 1 |
| `src/llm_wiki_engine/pack_interfaces.py:active_pack` | 3 | - | unresolved | 1 |
| `src/llm_wiki_engine/wiki_operations.py:_pack` | 2 | [src/llm_wiki_engine/wiki_operations.py](../modules/wiki_operations.md) | internal | 1 |
| `src/llm_wiki_engine/wiki_operations.py:_roots` | 6 | - | external | 2 |
| `src/llm_wiki_engine/wiki_operations.py:_roots` | 6 | - | unresolved | 1 |
| `src/llm_wiki_engine/wiki_operations.py:_roots` | 6 | [src/llm_wiki_engine/wiki_operations.py](../modules/wiki_operations.md) | internal | 1 |
| `src/llm_wiki_engine/sync_manifest.py:SyncManifest.load` | 11 | - | unresolved | 3 |
| `src/llm_wiki_engine/sync_manifest.py:SyncManifest.load` | 11 | - | external | 3 |
> Omission summary shows 8 of 162 groups; 154 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 246; effect analysis evaluated: 139, partial: 9, unavailable: 98. Counts include steps omitted from the displayed trace.

Collector observations for 148 source steps with known totals: observed: 673, emitted: 635, omitted: 38. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `lint` | `available` | `evaluated` | `available` | `9` | `9` | `0` |
| `_pack` | `available` | `evaluated` | `available` | `1` | `1` | `0` |
| `active_pack` | `available` | `evaluated` | `available` | `1` | `1` | `0` |
| `_ACTIVE_PACK.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `WikiOperationError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_roots` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `Path (src/llm_wiki_engine/wiki_operations.py:_roots)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path (src/llm_wiki_engine/wiki_operations.py:_roots)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `source.is_dir` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `WikiOperationError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `SyncManifest.load` | `available` | `evaluated` | `available` | `6` | `6` | `0` |
| `manifest_path.exists` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. lint"]
    s2["2. _pack"]
    s3["3. active_pack"]
    s4["4. _ACTIVE_PACK.get"]
    s5["5. WikiOperationError"]
    s6["6. _roots"]
    s7["7. Path (src/llm_wiki_engine/wiki_operations.py:_roots)"]
    s8["8. Path (src/llm_wiki_engine/wiki_operations.py:_roots)"]
    s9["9. source.is_dir"]
    s10["10. WikiOperationError"]
    s11["11. SyncManifest.load"]
    s12["12. manifest_path.exists"]
    s1 -->|"_pack(data not statically known)"| s2
    s2 -->|"active_pack(data not statically known)"| s3
    s3 -. "_ACTIVE_PACK.get(data not statically known)" .-> s4
    s2 -->|"WikiOperationError('no domain pack is active; run inside an engine operation')"| s5
    s1 -->|"_roots(request)"| s6
    s6 -. "Path (src/llm_wiki_engine/wiki_operations.py:_roots)(request.source_root)" .-> s7
    s6 -. "Path (src/llm_wiki_engine/wiki_operations.py:_roots)(request.wiki_root)" .-> s8
    s6 -. "source.is_dir(data not statically known)" .-> s9
    s6 -->|"WikiOperationError(...)"| s10
    s1 -->|"SyncManifest.load(wiki)"| s11
    s11 -. "manifest_path.exists(data not statically known)" .-> s12
    b0["mutation issues.append"]
    s1 -. "mutation issues.append" .-> b0
    b1["mutation issues.append"]
    s1 -. "mutation issues.append" .-> b1
    b2["mutation issues.append"]
    s1 -. "mutation issues.append" .-> b2
    b3["filesystem_read manifest_path.read_text"]
    s11 -. "filesystem_read manifest_path.read_text" .-> b3
    click s1 "../modules/wiki_operations.md"
    click s2 "../modules/wiki_operations.md"
    click s3 "../modules/pack_interfaces.md"
    click s5 "../modules/wiki_operations.md"
    click s6 "../modules/wiki_operations.md"
    click s10 "../modules/wiki_operations.md"
    click s11 "../modules/sync_manifest.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `lint` | `request: LintRequest` | `SyncManifestError`, `MANIFEST_FILENAME`, `INDEX_PAGE` | - | `LintReport(...)`, `LintReport(...)` |
| `_pack` | - | - | - | `pack` |
| `active_pack` | - | - | - | `_ACTIVE_PACK.get(...)` |
| `_ACTIVE_PACK.get` | - | - | - | - |
| `WikiOperationError` | - | - | - | - |
| `_roots` | `request: Any` | - | - | `(...)` |
| `Path (src/llm_wiki_engine/wiki_operations.py:_roots)` | - | - | - | - |
| `Path (src/llm_wiki_engine/wiki_operations.py:_roots)` | - | - | - | - |
| `source.is_dir` | - | - | - | - |
| `WikiOperationError` | - | - | - | - |
| `SyncManifest.load` | `wiki_dir: Path` | `MANIFEST_FILENAME`, `MANIFEST_FILENAME` | - | `manifest`, `cls.from_payload(...)` |
| `manifest_path.exists` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| lint | _pack | 404 | `_pack(data not statically known)` |
| _pack | active_pack | 119 | `active_pack(data not statically known)` |
| active_pack | _ACTIVE_PACK.get | 643 | `_ACTIVE_PACK.get(data not statically known)` |
| _pack | WikiOperationError | 121 | `WikiOperationError('no domain pack is active; run inside an engine operation')` |
| lint | _roots | 405 | `_roots(request)` |
| _roots | Path (src/llm_wiki_engine/wiki_operations.py:_roots) | 126 | `Path(request.source_root)` |
| _roots | Path (src/llm_wiki_engine/wiki_operations.py:_roots) | 127 | `Path(request.wiki_root)` |
| _roots | source.is_dir | 128 | `source.is_dir(data not statically known)` |
| _roots | WikiOperationError | 129 | `WikiOperationError(...)` |
| lint | SyncManifest.load | 408 | `SyncManifest.load(wiki)` |
| SyncManifest.load | manifest_path.exists | 1060 | `manifest_path.exists(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `issues.append` | `lint` | 423 |
| mutation | `issues.append` | `lint` | 425 |
| mutation | `issues.append` | `lint` | 429 |
| filesystem_read | `manifest_path.read_text` | `SyncManifest.load` | 1081 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `active_pack` | `_ACTIVE_PACK.get` | 643 |
| unresolved_call | `_roots` | `source.is_dir` | 128 |
| unresolved_call | `SyncManifest.load` | `manifest_path.exists` | 1060 |
| step_limit | `lint` | `first 12 steps` | 0 |
| truncated_flow | `lint` | `depth limit` | 0 |

## Behavior

This flow starts at `lint` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
