# prune_manifest_for_source_selection

**Entry point:** `prune_manifest_for_source_selection` (`api`)
**Source:** [sync_manifest](../modules/sync_manifest.md)
**Modules touched:** [sync_manifest](../modules/sync_manifest.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as prune_manifest_for_source_selection
    participant p1 as isinstance
    participant p2 as SyncManifestError
    participant p3 as SourceSelectionPruneResult
    participant p4 as set
    participant p5 as source_paths.update
    participant p6 as manifest.page_source_mappings.values
    participant p7 as tuple
    participant p8 as sorted
    participant p9 as is_selected
    participant p10 as manifest.page_source_mappings.items
    participant p11 as replace
    participant p12 as manifest.sources.items
    participant p13 as manifest.evidence_baselines.items
    participant p14 as manifest.tombstones.items
    participant p15 as pruned._validate_operational_state
    p0-->>p1: isinstance
    p0->>p2: SyncManifestError
    p0->>p3: SourceSelectionPruneResult
    p0->>p2: SyncManifestError
    p0-->>p4: set
    p0-->>p5: source_paths.update
    p0-->>p6: manifest.page_source_mappings.values
    p0-->>p7: tuple
    p0-->>p8: sorted
    p0-->>p9: is_selected
    p0->>p3: SourceSelectionPruneResult
    p0-->>p4: set
    p0-->>p10: manifest.page_source_mappings.items
    p0-->>p7: tuple
    p0-->>p8: sorted
    p0-->>p4: set
    p0-->>p4: set
    p0-->>p4: set
    p0-->>p11: replace
    p0-->>p12: manifest.sources.items
    p0-->>p13: manifest.evidence_baselines.items
    p0-->>p14: manifest.tombstones.items
    p0-->>p15: pruned._validate_operational_state
    p0->>p3: SourceSelectionPruneResult
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. prune_manifest_for_source_selection"]
    s2["2. isinstance"]
    s3["3. SyncManifestError"]
    s4["4. SourceSelectionPruneResult"]
    s5["5. SyncManifestError"]
    s6["6. set"]
    s7["7. source_paths.update"]
    s8["8. manifest.page_source_mappings.values"]
    s9["9. tuple"]
    s10["10. sorted"]
    s11["11. is_selected"]
    s12["12. SourceSelectionPruneResult"]
    s1 -. "isinstance(manifest, SyncManifest)" .-> s2
    s1 -->|"SyncManifestError('manifest', 'must be a SyncManifest')"| s3
    s1 -->|"SourceSelectionPruneResult(manifest, (...), (...))"| s4
    s1 -->|"SyncManifestError('source_selection', 'source snapshot must match the pruning selection policy')"| s5
    s1 -. "set(manifest.sources)" .-> s6
    s1 -. "source_paths.update(...)" .-> s7
    s1 -. "manifest.page_source_mappings.values(data not statically known)" .-> s8
    s1 -. "tuple(sorted(...))" .-> s9
    s1 -. "sorted(...)" .-> s10
    s1 -. "is_selected(path)" .-> s11
    s1 -->|"SourceSelectionPruneResult(manifest, (...), (...))"| s12
    b0["mutation source_paths.update"]
    s1 -. "mutation source_paths.update" .-> b0
    click s1 "../modules/sync_manifest.md"
    click s3 "../modules/sync_manifest.md"
    click s4 "../modules/sync_manifest.md"
    click s5 "../modules/sync_manifest.md"
    click s12 "../modules/sync_manifest.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `prune_manifest_for_source_selection` | `manifest: SyncManifest`, `policy: SourceSelectionPolicy \| None`, `source_snapshot: SourceSnapshot \| None` | `SyncManifest` | - | `SourceSelectionPruneResult(...)`, `SourceSelectionPruneResult(...)`, `SourceSelectionPruneResult(...)` |
| `isinstance` | - | - | - | - |
| `SyncManifestError` | - | - | - | - |
| `SourceSelectionPruneResult` | - | - | - | - |
| `SyncManifestError` | - | - | - | - |
| `set` | - | - | - | - |
| `source_paths.update` | - | - | - | - |
| `manifest.page_source_mappings.values` | - | - | - | - |
| `tuple` | - | - | - | - |
| `sorted` | - | - | - | - |
| `is_selected` | - | - | - | - |
| `SourceSelectionPruneResult` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| prune_manifest_for_source_selection | isinstance | 1614 | `isinstance(manifest, SyncManifest)` |
| prune_manifest_for_source_selection | SyncManifestError | 1615 | `SyncManifestError('manifest', 'must be a SyncManifest')` |
| prune_manifest_for_source_selection | SourceSelectionPruneResult | 1617 | `SourceSelectionPruneResult(manifest, (...), (...))` |
| prune_manifest_for_source_selection | SyncManifestError | 1626 | `SyncManifestError('source_selection', 'source snapshot must match the pruning selection policy')` |
| prune_manifest_for_source_selection | set | 1638 | `set(manifest.sources)` |
| prune_manifest_for_source_selection | source_paths.update | 1639 | `source_paths.update(...)` |
| prune_manifest_for_source_selection | manifest.page_source_mappings.values | 1640 | `manifest.page_source_mappings.values(data not statically known)` |
| prune_manifest_for_source_selection | tuple | 1642 | `tuple(sorted(...))` |
| prune_manifest_for_source_selection | sorted | 1643 | `sorted(...)` |
| prune_manifest_for_source_selection | is_selected | 1643 | `is_selected(path)` |
| prune_manifest_for_source_selection | SourceSelectionPruneResult | 1646 | `SourceSelectionPruneResult(manifest, (...), (...))` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `source_paths.update` | `prune_manifest_for_source_selection` | 1639 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `prune_manifest_for_source_selection` | `isinstance` | 1614 |
| unresolved_call | `prune_manifest_for_source_selection` | `manifest.page_source_mappings.values` | 1640 |
| external_call | `prune_manifest_for_source_selection` | `sorted` | 1643 |
| unresolved_call | `prune_manifest_for_source_selection` | `is_selected` | 1643 |
| step_limit | `prune_manifest_for_source_selection` | `first 12 steps` | 0 |

## Behavior

This flow starts at `prune_manifest_for_source_selection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
