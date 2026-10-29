# compose_doctor_report

**Entry point:** `compose_doctor_report` (`api`)
**Source:** [doctor_service](../modules/doctor_service.md)
**Modules touched:** [doctor_service](../modules/doctor_service.md), [health_policy](../modules/health_policy.md), [knowledge_observability](../modules/knowledge_observability.md), and 6 more

**Complete modules touched:**

- [doctor_service](../modules/doctor_service.md)
- [health_policy](../modules/health_policy.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compose_doctor_report
    participant p1 as _availability_section
    participant p2 as _freshness_section
    participant p3 as _governance_section
    participant p4 as _drift_section
    participant p5 as _verification_section
    participant p6 as _snapshot_section
    participant p7 as classify_health_sections
    participant p8 as _issues
    participant p9 as DoctorReport
    participant p10 as _knowledge_declared
    participant p11 as knowledge_freshness_disclosure
    participant p12 as SyncManifest.load
    participant p13 as StorageReadSession.read
    participant p14 as SyncManifest.from_payload
    participant p15 as decode_bytes
    participant p16 as StorageReadSession.recheck
    participant p17 as _require_relative_name
    participant p18 as _mapping_value
    participant p19 as StorageReadSession.phase
    participant p20 as _fail
    participant p21 as StorageReadSession.read_ranges
    participant p22 as ManifestStoreReader.materialize
    participant p23 as StorageReadSession.read_range
    participant p24 as canonical_bytes
    participant p25 as _copy_sources
    participant p26 as _legacy_operational_state
    participant p27 as _validate_exact_keys
    participant p28 as _copy_mapping
    participant p29 as isinstance (src/llm_wiki_cli/services….py:compose_doctor_report)
    participant p30 as unhealthy.append
    p0->>p1: _availability_section
    p0->>p2: _freshness_section
    p0->>p3: _governance_section
    p0->>p4: _drift_section
    p0->>p5: _verification_section
    p0->>p6: _snapshot_section
    p0->>p7: classify_health_sections
    p0->>p8: _issues
    p0->>p9: DoctorReport
    p1->>p10: _knowledge_declared
    p2->>p11: knowledge_freshness_disclosure
    p10->>p12: SyncManifest.load
    p12->>p13: StorageReadSession.read
    p12->>p14: SyncManifest.from_payload
    p12->>p15: decode_bytes
    p12->>p16: StorageReadSession.recheck
    p13->>p17: _require_relative_name
    p14->>p18: _mapping_value
    p16->>p19: StorageReadSession.phase
    p15->>p20: _fail
    p16->>p21: StorageReadSession.read_ranges
    p14->>p22: ManifestStoreReader.materialize
    p16->>p23: StorageReadSession.read_range
    p15->>p24: canonical_bytes
    p14->>p25: _copy_sources
    p14->>p26: _legacy_operational_state
    p14->>p27: _validate_exact_keys
    p14->>p28: _copy_mapping
    p0-->>p29: isinstance (src/llm_wiki_cli/services….py:compose_doctor_report)(lint, LintReport)
    p7-->>p30: unhealthy.append('source-selection-mismatch')
```

> Call sequence diagram shows 30 of 316 interactions; 286 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 91 (90 omitted); unresolved 1 of 70 (69 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/doctor_service.py:compose_doctor_report` | 1 | - | external | 5 |
| `src/llm_wiki_cli/services/doctor_service.py:_knowledge_declared` | 8 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/sync_manifest.py:SyncManifest.load` | 11 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/sync_manifest.py:SyncManifest.load` | 11 | - | external | 3 |
| `src/llm_wiki_cli/services/sync_manifest.py:SyncManifest.load` | 11 | [src/llm_wiki_cli/services/knowledge_storage_io.py](../modules/knowledge_storage_io.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_require_relative_name` | 20 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_require_relative_name` | 20 | [src/llm_wiki_cli/services/knowledge_storage.py](../modules/knowledge_storage.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:StorageReadSession.read` | 19 | [src/llm_wiki_cli/services/knowledge_storage.py](../modules/knowledge_storage.md) | internal | 3 |
> Omission summary shows 8 of 85 groups; 77 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 156; effect analysis evaluated: 92, partial: 6, unavailable: 58. Counts include steps omitted from the displayed trace.

Collector observations for 98 source steps with known totals: observed: 540, emitted: 527, omitted: 13. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `compose_doctor_report` | `available` | `evaluated` | `available` | `6` | `6` | `0` |
| `isinstance (src/llm_wiki_cli/services….py:compose_doctor_report)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services….py:compose_doctor_report)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services….py:compose_doctor_report)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services….py:compose_doctor_report)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_availability_section` | `available` | `evaluated` | `available` | `12` | `12` | `0` |
| `_knowledge_declared` | `available` | `evaluated` | `available` | `8` | `8` | `0` |
| `path.exists` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `path.is_symlink` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `SyncManifest.load` | `available` | `evaluated` | `available` | `6` | `6` | `0` |
| `manifest_path.exists` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. compose_doctor_report"]
    s2["2. isinstance (src/llm_wiki_cli/services….py:compose_doctor_report)"]
    s3["3. TypeError (src/llm_wiki_cli/services….py:compose_doctor_report)"]
    s4["4. isinstance (src/llm_wiki_cli/services….py:compose_doctor_report)"]
    s5["5. TypeError (src/llm_wiki_cli/services….py:compose_doctor_report)"]
    s6["6. Path"]
    s7["7. _availability_section"]
    s8["8. _knowledge_declared"]
    s9["9. path.exists"]
    s10["10. path.is_symlink"]
    s11["11. SyncManifest.load"]
    s12["12. manifest_path.exists"]
    s1 -. "isinstance (src/llm_wiki_cli/services….py:compose_doctor_report)(lint, LintReport)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services….py:compose_doctor_report)('lint must be a LintReport')" .-> s3
    s1 -. "isinstance (src/llm_wiki_cli/services….py:compose_doctor_report)(strict, bool)" .-> s4
    s1 -. "TypeError (src/llm_wiki_cli/services….py:compose_doctor_report)('strict must be a boolean')" .-> s5
    s1 -. "Path(wiki_dir)" .-> s6
    s1 -->|"_availability_section(lint, view, wiki_root)"| s7
    s7 -->|"_knowledge_declared(wiki_root)"| s8
    s8 -. "path.exists(data not statically known)" .-> s9
    s8 -. "path.is_symlink(data not statically known)" .-> s10
    s8 -->|"SyncManifest.load(wiki_root)"| s11
    s11 -. "manifest_path.exists(data not statically known)" .-> s12
    b0["filesystem_read manifest_path.read_text"]
    s11 -. "filesystem_read manifest_path.read_text" .-> b0
    click s1 "../modules/doctor_service.md"
    click s7 "../modules/doctor_service.md"
    click s8 "../modules/doctor_service.md"
    click s11 "../modules/sync_manifest.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `compose_doctor_report` | `lint: LintReport`, `strict: bool`, `wiki_dir: str`, `src_dir: str` | `LintReport` | - | `DoctorReport(...)` |
| `isinstance (src/llm_wiki_cli/services….py:compose_doctor_report)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services….py:compose_doctor_report)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services….py:compose_doctor_report)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services….py:compose_doctor_report)` | - | - | - | - |
| `Path` | - | - | - | - |
| `_availability_section` | `lint: LintReport`, `view: KnowledgeReadView \| None`, `wiki_root: Path` | `KnowledgeAvailability`, `KnowledgeAvailability`, `KnowledgeAvailability`, `KnowledgeAvailability`, `KnowledgeAvailability` | - | `{...}`, `{...}`, `{...}`, `{...}` |
| `_knowledge_declared` | `wiki_root: Path` | `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `GOVERNANCE_FILENAME`, `VERIFICATION_RECEIPT_FILENAME` | - | `True`, `False`, `...` |
| `path.exists` | - | - | - | - |
| `path.is_symlink` | - | - | - | - |
| `SyncManifest.load` | `wiki_dir: Path` | `MANIFEST_FILENAME`, `MANIFEST_FILENAME` | - | `manifest`, `cls.from_payload(...)` |
| `manifest_path.exists` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compose_doctor_report | isinstance (src/llm_wiki_cli/services….py:compose_doctor_report) | 190 | `isinstance(lint, LintReport)` |
| compose_doctor_report | TypeError (src/llm_wiki_cli/services….py:compose_doctor_report) | 191 | `TypeError('lint must be a LintReport')` |
| compose_doctor_report | isinstance (src/llm_wiki_cli/services….py:compose_doctor_report) | 192 | `isinstance(strict, bool)` |
| compose_doctor_report | TypeError (src/llm_wiki_cli/services….py:compose_doctor_report) | 193 | `TypeError('strict must be a boolean')` |
| compose_doctor_report | Path | 196 | `Path(wiki_dir)` |
| compose_doctor_report | _availability_section | 197 | `_availability_section(lint, view, wiki_root)` |
| _availability_section | _knowledge_declared | 314 | `_knowledge_declared(wiki_root)` |
| _knowledge_declared | path.exists | 348 | `path.exists(data not statically known)` |
| _knowledge_declared | path.is_symlink | 348 | `path.is_symlink(data not statically known)` |
| _knowledge_declared | SyncManifest.load | 351 | `SyncManifest.load(wiki_root)` |
| SyncManifest.load | manifest_path.exists | 1160 | `manifest_path.exists(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `manifest_path.read_text` | `SyncManifest.load` | 1181 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `compose_doctor_report` | `isinstance` | 190 |
| external_call | `compose_doctor_report` | `TypeError` | 191 |
| external_call | `compose_doctor_report` | `isinstance` | 192 |
| external_call | `compose_doctor_report` | `TypeError` | 193 |
| unresolved_call | `_knowledge_declared` | `path.exists` | 348 |
| unresolved_call | `_knowledge_declared` | `path.is_symlink` | 348 |
| unresolved_call | `SyncManifest.load` | `manifest_path.exists` | 1160 |
| step_limit | `compose_doctor_report` | `first 12 steps` | 0 |
| truncated_flow | `compose_doctor_report` | `depth limit` | 0 |

## Behavior

This flow starts at `compose_doctor_report` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
