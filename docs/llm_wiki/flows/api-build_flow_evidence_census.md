# build_flow_evidence_census

**Entry point:** `build_flow_evidence_census` (`api`)
**Source:** [documentation_run_dependencies](../modules/documentation_run_dependencies.md)
**Modules touched:** [calibration_contracts](../modules/calibration_contracts.md), [documentation_run_dependencies](../modules/documentation_run_dependencies.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_flow_evidence_census
    participant p1 as build_p0_calibration_shadow
    participant p2 as validate_flow_evidence_census
    participant p3 as get
    participant p4 as DocumentationCalibrationError
    participant p5 as isinstance
    p0->>p1: build_p0_calibration_shadow
    p1->>p2: validate_flow_evidence_census
    p2-->>p3: get
    p2->>p4: DocumentationCalibrationError
    p2-->>p3: get
    p2->>p4: DocumentationCalibrationError
    p2-->>p3: get
    p2-->>p5: isinstance
    p2-->>p5: isinstance
    p2-->>p3: get
    p2->>p4: DocumentationCalibrationError
    p2-->>p3: get
    p2-->>p3: get
    p2->>p4: DocumentationCalibrationError
    p2-->>p3: get
    p2-->>p3: get
    p2-->>p3: get
    p2-->>p5: isinstance
    p2-->>p5: isinstance
    p2->>p4: DocumentationCalibrationError
    p2-->>p5: isinstance
    p2->>p4: DocumentationCalibrationError
    p2-->>p5: isinstance
    p2->>p4: DocumentationCalibrationError
    p2->>p4: DocumentationCalibrationError
    p2-->>p3: get
    p2->>p4: DocumentationCalibrationError
    p2-->>p5: isinstance
    p2-->>p3: get
    p2-->>p3: get
```

> Call sequence diagram shows 30 of 185 interactions; 155 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_flow_evidence_census"]
    s2["2. build_p0_calibration_shadow"]
    s3["3. validate_flow_evidence_census"]
    s4["4. get"]
    s5["5. DocumentationCalibrationError"]
    s6["6. get"]
    s7["7. DocumentationCalibrationError"]
    s8["8. get"]
    s9["9. isinstance"]
    s10["10. isinstance"]
    s11["11. get"]
    s12["12. DocumentationCalibrationError"]
    s1 -->|"implementation(wiki_dir, source_root=source_root, source_revision=source_revision, source_fingerprint=source_fingerprint, dependency_evidence=dependency_eviden…"| s2
    s2 -->|"validate_flow_evidence_census(census)"| s3
    s3 -. "payload.get('schema_version')" .-> s4
    s3 -->|"DocumentationCalibrationError('Unsupported flow-census schema_version.')"| s5
    s3 -. "payload.get('priority_blind')" .-> s6
    s3 -->|"DocumentationCalibrationError('Flow census must remain priority_blind.')"| s7
    s3 -. "payload.get('population')" .-> s8
    s3 -. "isinstance(population, Mapping)" .-> s9
    s3 -. "isinstance(population.get(...), bool)" .-> s10
    s3 -. "population.get('complete')" .-> s11
    s3 -->|"DocumentationCalibrationError('Flow census population is malformed.')"| s12
    b0["mutation structural_controls.append"]
    s2 -. "mutation structural_controls.append" .-> b0
    b1["mutation shadow_items.append"]
    s2 -. "mutation shadow_items.append" .-> b1
    b2["mutation family_ids.add"]
    s3 -. "mutation family_ids.add" .-> b2
    b3["mutation family_members.extend"]
    s3 -. "mutation family_members.extend" .-> b3
    b4["mutation family_by_member.update"]
    s3 -. "mutation family_by_member.update" .-> b4
    click s1 "../modules/documentation_run_dependencies.md"
    click s2 "../modules/calibration_contracts.md"
    click s3 "../modules/calibration_contracts.md"
    click s5 "../modules/calibration_contracts.md"
    click s7 "../modules/calibration_contracts.md"
    click s12 "../modules/calibration_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_flow_evidence_census` | `wiki_dir: str`, `source_root: Optional[str]`, `source_revision: str`, `source_fingerprint: str`, `dependency_evidence: Optional[Mapping[str, Any]]`, `tool_revision: str`, `allow_surface_fallback: bool` | - | - | `implementation(...)` |
| `build_p0_calibration_shadow` | `worklist: Mapping[str, Any]`, `census: Mapping[str, Any]`, `candidate_records: Optional[Iterable[Mapping[str, Any]]]`, `policy_version: str` | `Mapping`, `Mapping`, `_CALIBRATION_PRIORITIES`, `P0_CALIBRATION_SHADOW_SCHEMA_VERSION` | `current_by_flow[...]`, `candidates[...]` | `{...}` |
| `validate_flow_evidence_census` | `payload: Mapping[str, Any]` | `P0_FLOW_CENSUS_SCHEMA_VERSION`, `Mapping`, `Mapping`, `_SOURCE_PROVENANCE`, `Mapping`, `Mapping`, `Mapping`, `Mapping` | - | - |
| `get` | - | - | - | - |
| `DocumentationCalibrationError` | - | - | - | - |
| `get` | - | - | - | - |
| `DocumentationCalibrationError` | - | - | - | - |
| `get` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `get` | - | - | - | - |
| `DocumentationCalibrationError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_flow_evidence_census | build_p0_calibration_shadow | 138 | `implementation(wiki_dir, source_root=source_root, source_revision=source_revision, source_fingerprint=source_fingerprint, dependency_evidence=dependency_evidence, tool_revision=tool_revision, allow_surface_fallback=allow_surface_fallback)` |
| build_p0_calibration_shadow | validate_flow_evidence_census | 381 | `validate_flow_evidence_census(census)` |
| validate_flow_evidence_census | get | 237 | `payload.get('schema_version')` |
| validate_flow_evidence_census | DocumentationCalibrationError | 238 | `DocumentationCalibrationError('Unsupported flow-census schema_version.')` |
| validate_flow_evidence_census | get | 239 | `payload.get('priority_blind')` |
| validate_flow_evidence_census | DocumentationCalibrationError | 240 | `DocumentationCalibrationError('Flow census must remain priority_blind.')` |
| validate_flow_evidence_census | get | 241 | `payload.get('population')` |
| validate_flow_evidence_census | isinstance | 242 | `isinstance(population, Mapping)` |
| validate_flow_evidence_census | isinstance | 242 | `isinstance(population.get(...), bool)` |
| validate_flow_evidence_census | get | 243 | `population.get('complete')` |
| validate_flow_evidence_census | DocumentationCalibrationError | 245 | `DocumentationCalibrationError('Flow census population is malformed.')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `structural_controls.append` | `build_p0_calibration_shadow` | 398 |
| mutation | `shadow_items.append` | `build_p0_calibration_shadow` | 430 |
| mutation | `family_ids.add` | `validate_flow_evidence_census` | 351 |
| mutation | `family_members.extend` | `validate_flow_evidence_census` | 353 |
| mutation | `family_by_member.update` | `validate_flow_evidence_census` | 354 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_flow_evidence_census` | `payload.get` | 237 |
| unresolved_call | `validate_flow_evidence_census` | `payload.get` | 239 |
| unresolved_call | `validate_flow_evidence_census` | `payload.get` | 241 |
| unresolved_call | `validate_flow_evidence_census` | `isinstance` | 242 |
| unresolved_call | `validate_flow_evidence_census` | `population.get` | 243 |
| step_limit | `build_flow_evidence_census` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_flow_evidence_census` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
