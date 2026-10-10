# build_flow_evidence_census

**Entry point:** `build_flow_evidence_census` (`api`)
**Source:** [documentation_run_dependencies](../modules/documentation_run_dependencies.md)
**Modules touched:** [calibration_contracts](../modules/calibration_contracts.md), [documentation_run_dependencies](../modules/documentation_run_dependencies.md), [validation](../modules/validation.md), and 1 more

**Complete modules touched:**

- [calibration_contracts](../modules/calibration_contracts.md)
- [documentation_run_dependencies](../modules/documentation_run_dependencies.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_flow_evidence_census (src/llm_wiki_cli/services…ation_run/dependencies.py)
    participant p1 as build_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py)
    participant p2 as Path(…).expanduser (src/llm_wiki_cli/services…d_flow_evidence_census, 1)
    participant p3 as Path
    participant p4 as wiki.is_dir
    participant p5 as DocumentationCalibrationError
    participant p6 as surface_path.exists
    participant p7 as _fallback_flow_records
    participant p8 as _read_json_mapping
    participant p9 as surface.get
    participant p10 as isinstance (src/llm_wiki_cli/services…uild_flow_evidence_census)
    participant p11 as Path(…).expanduser().resolve
    participant p12 as Path(…).expanduser (src/llm_wiki_cli/services…uild_flow_evidence_census)
    participant p13 as _dependency_metric_map
    participant p14 as set (src/llm_wiki_cli/services…uild_flow_evidence_census)
    participant p15 as _required_flow_id
    participant p16 as seen_flow_ids.add
    participant p17 as capsules.append
    participant p18 as _flow_capsule
    participant p19 as capsules.sort
    participant p20 as item[…].casefold (src/llm_wiki_cli/services…uild_flow_evidence_census)
    participant p21 as defaultdict
    participant p22 as str (src/llm_wiki_cli/services…uild_flow_evidence_census)
    participant p23 as families_by_id[…].append
    p0->>p1: build_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py)
    p1-->>p2: Path(…).expanduser (src/llm_wiki_cli/services…d_flow_evidence_census, 1)
    p1-->>p3: Path(wiki_dir)
    p1-->>p4: wiki.is_dir
    p1->>p5: DocumentationCalibrationError
    p1-->>p6: surface_path.exists
    p1->>p7: _fallback_flow_records
    p1->>p8: _read_json_mapping
    p1-->>p9: surface.get('flows')
    p1->>p7: _fallback_flow_records
    p1-->>p10: isinstance (src/llm_wiki_cli/services…uild_flow_evidence_census)(raw_flows, list)
    p1->>p5: DocumentationCalibrationError
    p1-->>p11: Path(…).expanduser().resolve
    p1-->>p12: Path(…).expanduser (src/llm_wiki_cli/services…uild_flow_evidence_census)
    p1-->>p3: Path(source_root)
    p1->>p13: _dependency_metric_map
    p1-->>p14: set (src/llm_wiki_cli/services…uild_flow_evidence_census)
    p1-->>p10: isinstance (src/llm_wiki_cli/services…uild_flow_evidence_census)(raw, Mapping)
    p1->>p5: DocumentationCalibrationError
    p1->>p15: _required_flow_id
    p1->>p5: DocumentationCalibrationError
    p1-->>p16: seen_flow_ids.add(flow_id)
    p1-->>p17: capsules.append(_flow_capsule(...))
    p1->>p18: _flow_capsule
    p1-->>p19: capsules.sort(key=...)
    p1-->>p20: item[…].casefold (src/llm_wiki_cli/services…uild_flow_evidence_census)
    p1-->>p21: defaultdict(list)
    p1-->>p22: str (src/llm_wiki_cli/services…uild_flow_evidence_census)(...)
    p1-->>p23: families_by_id[…].append(str(...))
    p1-->>p22: str (src/llm_wiki_cli/services…uild_flow_evidence_census)(capsule[...])
```

> Call sequence diagram shows 30 of 406 interactions; 376 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 8 of 137 (129 omitted); unresolved 11 of 164 (153 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/calibration/contracts.py:_fallback_flow_records` | 8 | - | unresolved | 8 |
| `src/llm_wiki_cli/services/calibration/contracts.py:_fallback_flow_records` | 8 | [src/llm_wiki_cli/services/wiki_surface.py](../modules/wiki_surface.md) | internal | 1 |
| `src/llm_wiki_cli/services/wiki_surface.py:is_safe_page_id` | 14 | - | external | 3 |
| `src/llm_wiki_cli/services/wiki_surface.py:is_safe_page_id` | 14 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/wiki_surface.py:is_safe_page_id` | 14 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:is_portable_path_component` | 20 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_portable_path_component` | 21 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/validation.py:require_portable_path_component` | 21 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 5 |
> Omission summary shows 8 of 74 groups; 66 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_flow_evidence_census (src/llm_wiki_cli/services…ation_run/dependencies.py)"]
    s2["2. build_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py)"]
    s3["3. Path(…).expanduser (src/llm_wiki_cli/services…d_flow_evidence_census, 1)"]
    s4["4. Path"]
    s5["5. wiki.is_dir"]
    s6["6. DocumentationCalibrationError"]
    s7["7. surface_path.exists"]
    s8["8. _fallback_flow_records"]
    s9["9. flows_dir.is_symlink"]
    s10["10. flows_dir.is_dir"]
    s11["11. flows_dir.glob"]
    s12["12. path.is_file"]
    s1 -->|"build_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py)(…)"| s2
    s2 -. "Path(…).expanduser (src/llm_wiki_cli/services…d_flow_evidence_census, 1)(data not statically known)" .-> s3
    s2 -. "Path(wiki_dir)" .-> s4
    s2 -. "wiki.is_dir(data not statically known)" .-> s5
    s2 -->|"DocumentationCalibrationError(...)"| s6
    s2 -. "surface_path.exists(data not statically known)" .-> s7
    s2 -->|"_fallback_flow_records(wiki)"| s8
    s8 -. "flows_dir.is_symlink(data not statically known)" .-> s9
    s8 -. "flows_dir.is_dir(data not statically known)" .-> s10
    s8 -. "flows_dir.glob('*.md')" .-> s11
    s8 -. "path.is_file(data not statically known)" .-> s12
    b0["mutation seen_flow_ids.add"]
    s2 -. "mutation seen_flow_ids.add" .-> b0
    b1["mutation capsules.append"]
    s2 -. "mutation capsules.append" .-> b1
    b2["mutation capsules.sort"]
    s2 -. "mutation capsules.sort" .-> b2
    b3["mutation records.append"]
    s8 -. "mutation records.append" .-> b3
    click s1 "../modules/documentation_run_dependencies.md"
    click s2 "../modules/calibration_contracts.md"
    click s6 "../modules/calibration_contracts.md"
    click s8 "../modules/calibration_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_flow_evidence_census (src/llm_wiki_cli/services…ation_run/dependencies.py)` | `wiki_dir: str`, `source_root: Optional[str]`, `source_revision: str`, `source_fingerprint: str`, `dependency_evidence: Optional[Mapping[str, Any]]`, `tool_revision: str`, `allow_surface_fallback: bool` | - | - | `implementation(...)` |
| `build_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py)` | `wiki_dir: str`, `source_root: Optional[str]`, `source_revision: str`, `source_fingerprint: str`, `dependency_evidence: Optional[Mapping[str, Any]]`, `tool_revision: str`, `allow_surface_fallback: bool` | `SURFACE_INDEX_FILENAME`, `Mapping`, `P0_FLOW_CENSUS_SCHEMA_VERSION` | `family_basis[...]` | `payload` |
| `Path(…).expanduser (src/llm_wiki_cli/services…d_flow_evidence_census, 1)` | - | - | - | - |
| `Path` | - | - | - | - |
| `wiki.is_dir` | - | - | - | - |
| `DocumentationCalibrationError` | - | - | - | - |
| `surface_path.exists` | - | - | - | - |
| `_fallback_flow_records` | `wiki: Path` | - | - | `[...]`, `sorted(...)` |
| `flows_dir.is_symlink` | - | - | - | - |
| `flows_dir.is_dir` | - | - | - | - |
| `flows_dir.glob` | - | - | - | - |
| `path.is_file` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_flow_evidence_census (src/llm_wiki_cli/services…ation_run/dependencies.py) | build_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py) | 143 | `implementation(wiki_dir, source_root=source_root, source_revision=source_revision, source_fingerprint=source_fingerprint, dependency_evidence=dependency_evidence, tool_revision=tool_revision, allow_surface_fallback=allow_surface_fallback)` |
| build_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py) | Path(…).expanduser (src/llm_wiki_cli/services…d_flow_evidence_census, 1) | 125 | `Path(wiki_dir).expanduser(data not statically known)` |
| build_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py) | Path | 125 | `Path(wiki_dir)` |
| build_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py) | wiki.is_dir | 126 | `wiki.is_dir(data not statically known)` |
| build_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py) | DocumentationCalibrationError | 127 | `DocumentationCalibrationError(...)` |
| build_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py) | surface_path.exists | 131 | `surface_path.exists(data not statically known)` |
| build_flow_evidence_census (src/llm_wiki_cli/services/calibration/contracts.py) | _fallback_flow_records | 132 | `_fallback_flow_records(wiki)` |
| _fallback_flow_records | flows_dir.is_symlink | 936 | `flows_dir.is_symlink(data not statically known)` |
| _fallback_flow_records | flows_dir.is_dir | 936 | `flows_dir.is_dir(data not statically known)` |
| _fallback_flow_records | flows_dir.glob | 939 | `flows_dir.glob('*.md')` |
| _fallback_flow_records | path.is_file | 941 | `path.is_file(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen_flow_ids.add` | `build_flow_evidence_census` | 155 |
| mutation | `capsules.append` | `build_flow_evidence_census` | 156 |
| mutation | `capsules.sort` | `build_flow_evidence_census` | 165 |
| mutation | `records.append` | `_fallback_flow_records` | 942 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `build_flow_evidence_census` | `Path(wiki_dir).expanduser` | 125 |
| unresolved_call | `build_flow_evidence_census` | `wiki.is_dir` | 126 |
| unresolved_call | `build_flow_evidence_census` | `surface_path.exists` | 131 |
| unresolved_call | `_fallback_flow_records` | `flows_dir.is_symlink` | 936 |
| unresolved_call | `_fallback_flow_records` | `flows_dir.is_dir` | 936 |
| unresolved_call | `_fallback_flow_records` | `flows_dir.glob` | 939 |
| unresolved_call | `_fallback_flow_records` | `path.is_file` | 941 |
| step_limit | `build_flow_evidence_census` | `first 12 steps` | 0 |
| truncated_flow | `build_flow_evidence_census` | `depth limit` | 0 |

## Behavior

This flow starts at `build_flow_evidence_census` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
