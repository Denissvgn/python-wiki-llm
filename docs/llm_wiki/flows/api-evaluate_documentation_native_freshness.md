# evaluate_documentation_native_freshness

**Entry point:** `evaluate_documentation_native_freshness` (`api`)
**Source:** [documentation_native](../modules/documentation_native.md)
**Modules touched:** [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), [config](../modules/config.md), [documentation_native](../modules/documentation_native.md), and 23 more

**Complete modules touched:**

- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [documentation_native](../modules/documentation_native.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [inventory_cache](../modules/inventory_cache.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [markdown_sections](../modules/markdown_sections.md)
- [packages](../modules/packages.md)
- [plugins](../modules/plugins.md)
- [resource_diagnostics](../modules/resource_diagnostics.md)
- [section_ownership](../modules/section_ownership.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as evaluate_documentation_native_freshness
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as _native_source_snapshot_preflight
    participant p4 as _validated_directory
    participant p5 as expanduser
    participant p6 as Path
    participant p7 as lstat
    participant p8 as DocumentationNativeError
    participant p9 as S_ISLNK
    participant p10 as S_ISDIR
    participant p11 as resolve
    participant p12 as resolve_source_selection
    participant p13 as SourceSelectionError
    participant p14 as _override_text
    participant p15 as fspath
    participant p16 as _selection_path
    participant p17 as _require_selection_path
    participant p18 as require_repository_relative_path
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: _native_source_snapshot_preflight
    p3->>p4: _validated_directory
    p4-->>p5: expanduser
    p4-->>p6: Path
    p4-->>p7: lstat
    p4->>p8: DocumentationNativeError
    p4-->>p9: S_ISLNK
    p4-->>p10: S_ISDIR
    p4->>p8: DocumentationNativeError
    p4-->>p11: resolve
    p3->>p12: resolve_source_selection
    p12-->>p11: resolve
    p12-->>p6: Path
    p12->>p13: SourceSelectionError
    p12->>p14: _override_text
    p14-->>p15: fspath
    p14->>p13: SourceSelectionError
    p14-->>p1: isinstance
    p14->>p13: SourceSelectionError
    p14->>p16: _selection_path
    p16->>p17: _require_selection_path
    p17->>p18: require_repository_relative_path
    p17->>p13: SourceSelectionError
    p17->>p13: SourceSelectionError
    p17->>p13: SourceSelectionError
    p17->>p13: SourceSelectionError
```

> Call sequence diagram shows 30 of 2848 interactions; 2818 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. evaluate_documentation_native_freshness"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. isinstance"]
    s5["5. TypeError"]
    s6["6. _native_source_snapshot_preflight"]
    s7["7. _validated_directory"]
    s8["8. expanduser"]
    s9["9. Path"]
    s10["10. lstat"]
    s11["11. DocumentationNativeError"]
    s12["12. S_ISLNK"]
    s1 -. "isinstance(knowledge, KnowledgeIndex)" .-> s2
    s1 -. "TypeError('knowledge must be a KnowledgeIndex')" .-> s3
    s1 -. "isinstance(manifest, SyncManifest)" .-> s4
    s1 -. "TypeError('manifest must be a SyncManifest')" .-> s5
    s1 -->|"_native_source_snapshot_preflight(source_root=source_root, manifest=manifest, source_selection=source_selection, operation='native freshness')"| s6
    s6 -->|"_validated_directory(source_root, 'source_root')"| s7
    s7 -. "Path(value).expanduser(data not statically known)" .-> s8
    s7 -. "Path(value)" .-> s9
    s7 -. "candidate.lstat(data not statically known)" .-> s10
    s7 -->|"DocumentationNativeError(...)"| s11
    s7 -. "stat.S_ISLNK(metadata.st_mode)" .-> s12
    b0["mutation missing_source_paths.add"]
    s1 -. "mutation missing_source_paths.add" .-> b0
    b1["mutation reasons.append"]
    s1 -. "mutation reasons.append" .-> b1
    b2["mutation reasons.append"]
    s1 -. "mutation reasons.append" .-> b2
    b3["mutation reasons.append"]
    s1 -. "mutation reasons.append" .-> b3
    click s1 "../modules/documentation_native.md"
    click s6 "../modules/documentation_native.md"
    click s7 "../modules/documentation_native.md"
    click s11 "../modules/documentation_native.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `evaluate_documentation_native_freshness` | `knowledge: KnowledgeIndex`, `manifest: SyncManifest`, `source_root: str \| Path`, `trust_source_plugins: bool`, `helper_cache_dir: str \| Path \| None`, `source_selection: str \| Path \| None` | `KnowledgeIndex`, `SyncManifest`, `ObservationScope`, `RUNTIME_GENERATION_OPTION_DEFAULTS`, `RUNTIME_GENERATION_OPTION_DEFAULTS`, `PageKind`, `ComputedFreshness` | - | `DocumentationNativeFreshness(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_native_source_snapshot_preflight` | `source_root: str \| Path`, `manifest: SyncManifest`, `source_selection: str \| Path \| None`, `operation: str`, `allow_same_path_identity_update: bool` | `SourceSelectionError`, `SourceSnapshotError` | - | `(...)` |
| `_validated_directory` | `value: str \| Path`, `field_name: str` | - | - | `candidate.resolve(...)` |
| `expanduser` | - | - | - | - |
| `Path` | - | - | - | - |
| `lstat` | - | - | - | - |
| `DocumentationNativeError` | - | - | - | - |
| `S_ISLNK` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| evaluate_documentation_native_freshness | isinstance | 202 | `isinstance(knowledge, KnowledgeIndex)` |
| evaluate_documentation_native_freshness | TypeError | 203 | `TypeError('knowledge must be a KnowledgeIndex')` |
| evaluate_documentation_native_freshness | isinstance | 204 | `isinstance(manifest, SyncManifest)` |
| evaluate_documentation_native_freshness | TypeError | 205 | `TypeError('manifest must be a SyncManifest')` |
| evaluate_documentation_native_freshness | _native_source_snapshot_preflight | 206 | `_native_source_snapshot_preflight(source_root=source_root, manifest=manifest, source_selection=source_selection, operation='native freshness')` |
| _native_source_snapshot_preflight | _validated_directory | 155 | `_validated_directory(source_root, 'source_root')` |
| _validated_directory | expanduser | 1078 | `Path(value).expanduser(data not statically known)` |
| _validated_directory | Path | 1078 | `Path(value)` |
| _validated_directory | lstat | 1080 | `candidate.lstat(data not statically known)` |
| _validated_directory | DocumentationNativeError | 1082 | `DocumentationNativeError(...)` |
| _validated_directory | S_ISLNK | 1085 | `stat.S_ISLNK(metadata.st_mode)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `missing_source_paths.add` | `evaluate_documentation_native_freshness` | 242 |
| mutation | `reasons.append` | `evaluate_documentation_native_freshness` | 281 |
| mutation | `reasons.append` | `evaluate_documentation_native_freshness` | 283 |
| mutation | `reasons.append` | `evaluate_documentation_native_freshness` | 293 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `evaluate_documentation_native_freshness` | `isinstance` | 202 |
| unresolved_call | `evaluate_documentation_native_freshness` | `TypeError` | 203 |
| unresolved_call | `evaluate_documentation_native_freshness` | `isinstance` | 204 |
| unresolved_call | `evaluate_documentation_native_freshness` | `TypeError` | 205 |
| unresolved_call | `_validated_directory` | `Path(value).expanduser` | 1078 |
| unresolved_call | `_validated_directory` | `candidate.lstat` | 1080 |
| external_call | `_validated_directory` | `stat.S_ISLNK` | 1085 |
| step_limit | `evaluate_documentation_native_freshness` | `first 12 steps` | 0 |
| truncated_flow | `evaluate_documentation_native_freshness` | `depth limit` | 0 |

## Behavior

This flow starts at `evaluate_documentation_native_freshness` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
